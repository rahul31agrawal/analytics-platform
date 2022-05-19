from cgi import print_arguments
from flask import g, redirect, flash, session
from flask_appbuilder._compat import as_unicode
from flask_appbuilder.api import expose
from flask_appbuilder.security.forms import LoginForm_db
from flask_appbuilder.security.views import AuthDBView
from flask_login import login_user

from superset import config
from superset.security import SupersetSecurityManager
import requests
import base64
import logging
from urllib.parse import urlencode
from xml.etree import ElementTree


class AbinitioAuthView(AuthDBView):
    LOGIN_FAILED_AT_GATEWAY = "Login failed at gateway, please retry after some time."

    def __init__(self):
        super(AbinitioAuthView, self).__init__()
        self.auth_gateway = AbinitioAuthGateway(config.ABINITIO_GATEWAY_CONFIG)

    @expose("/login/", methods=["GET", "POST"])
    def login(self):
        if g.user is not None and g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_index)

        form = LoginForm_db()
        if form.validate_on_submit():
            username = form.username.data
            try:
                roles = self.auth_gateway.get_user_roles(username, form.password.data)
            except Exception as e:
                logging.error("Failed at auth gateway", e)
                flash(as_unicode(self.LOGIN_FAILED_AT_GATEWAY), "warning")
                return redirect(self.appbuilder.get_url_for_login)

            user = None
            if roles and len(roles) > 0:
                user = self.appbuilder.sm.find_user(username=username)
                
                # User does not exist, create one if auto user registration.
                if user is None:
                    user = self.appbuilder.sm.add_user(
                        username=username,
                        first_name=username,
                        last_name="-",
                        email=username + '@email.notfound',
                        role=self.appbuilder.sm.find_role(roles[0]),
                    )
                else:
                    #User exist but is inactive, then activate it
                    if not user.is_active:
                        user.active = True
                        self.appbuilder.sm.update_user(user)

                    # User exist but the role is updated in AG - Update the role on superset
                    if (str(user.roles[0]) != roles[0]):
                        user.roles = [self.appbuilder.sm.find_role(roles[0])]
                        self.appbuilder.sm.update_user(user)

            if not user:
                #User not in AG but is presernt in IOU - deactivate user
                user = self.appbuilder.sm.find_user(username=username)
                if user and user.is_active:
                    user.active = False
                    self.appbuilder.sm.update_user(user)
                
                flash(as_unicode(self.invalid_login_message), "warning")
                return redirect(self.appbuilder.get_url_for_login)

            login_user(user, remember=False)
            return redirect(self.appbuilder.get_url_for_index)

        return self.render_template(
            self.login_template, title=self.title, form=form, appbuilder=self.appbuilder
        )


class AbinitioAuthGateway:
    def __init__(self, gateway_config):
        self.gateway_config = gateway_config

    def get_product_id(self, product_name):
        return product_name.replace(" ", "")

    def get_auth_header(self, user, password):
        auth = base64.b64encode(("{}:{}".format(user, password)).encode('utf-8'))
        auth = "Basic {}".format(auth.decode('ascii'))
        return auth

    def register_product(self):
        auth = self.get_auth_header(self.gateway_config["api_user"], self.gateway_config["api_password"])
        params = {
            "productId": self.get_product_id(self.gateway_config["product_name"]),
            "productName": self.gateway_config["product_name"]
        }
        encoded_params = urlencode(params)
        resp = requests.get("http://{}:{}{}{}?{}".format(
                self.gateway_config["host"],
                self.gateway_config["port"],
                self.gateway_config["root_path"],
                self.gateway_config["register_product_path"],
                encoded_params
            ),
            headers={"Authorization": auth})
        if resp.status_code != 200:
            raise Exception('Failed auth call register_product {}'.format(resp.status_code))
        return True

    def get_user_roles(self, username, password):
        auth = self.get_auth_header(username, password)
        params = {
            "userName": username,
            "productName": self.gateway_config["product_name"]
        }
        encoded_params = urlencode(params)
        url = "http://{}:{}{}{}?{}".format(
                self.gateway_config["host"],
                self.gateway_config["port"],
                self.gateway_config["root_path"],
                self.gateway_config["get_user_roles_path"],
                encoded_params
            )
        resp = requests.get(
            url,
            headers={"Authorization": auth, "content-type": "text/xml"})
        if resp.status_code != 200:
            raise Exception('Failed auth call get_user_roles {}'.format(resp.status_code))
        parsed_resp = ElementTree.fromstring(resp.content)
        roles = []
        for role in parsed_resp.find('roles').iter('role'):
            if role.attrib['id'] in self.gateway_config["role_mapping"]:
                roles.append(self.gateway_config["role_mapping"][role.attrib['id']])
        return roles

    def post_user_roles(self):
        auth = self.get_auth_header(self.gateway_config["api_user"], self.gateway_config["api_password"])
        roles_str = ""
        for role_id in self.gateway_config["role_mapping"]:
            roles_str = roles_str + '<role id="{}" name="{}" description="{}"> <childRoles/> </role>'\
                .format(role_id, self.gateway_config["role_mapping"][role_id], self.gateway_config["role_mapping"][role_id])
        roles_payload = '<?xml version="1.0" encoding="UTF-8"?>' \
            + '<product apmClientVersion="1.0" name="IOU Core"><description>IOU Core</description><roles>' \
            + roles_str + '</roles></product>'
        params = {
            "userName": self.gateway_config["api_user"],
            "productName": self.gateway_config["product_name"]
        }
        encoded_params = urlencode(params)
        resp = requests.post("http://{}:{}{}{}?{}".format(
                self.gateway_config["host"],
                self.gateway_config["port"],
                self.gateway_config["root_path"],
                self.gateway_config["publish_roles_path"],
                encoded_params
            ),
            headers={"Authorization": auth, "content-type": "text/xml"},
            data=roles_payload)
        if resp.status_code != 200:
            raise Exception('Failed auth call post_user_roles {}'.format(resp.status_code))
        return True


class AbinitioSecurityManager(SupersetSecurityManager):
    authdbview = AbinitioAuthView

    def __init__(self, appbuilder):
        super(AbinitioSecurityManager, self).__init__(appbuilder)
        self.gateway_config = config.ABINITIO_GATEWAY_CONFIG
        self.abinitio_gateway = AbinitioAuthGateway(self.gateway_config)
