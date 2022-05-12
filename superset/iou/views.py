from flask import request, g, json
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget
from flask_appbuilder.forms import GeneralModelConverter
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.sqla.filters import FilterGreater,FilterNotEqual
from superset.views.base import SupersetModelView
from superset.config import AUDIT_LOGGING_PATH
from superset import db

from wtforms.fields import StringField, SelectField
from uuid import uuid4

from .widgets import BS3TextFieldROWidget
import datetime
import re
import logging

from .models import (
    CompanyBrand,
    FulfillmentAction,
    FulfillmentActionType,
    FulfillmentActionTypeAttribute,
    FulfillmentActionValue,
    Loan,
    LoanChannel,
    LoanTransaction,
    LoanTransactionType,
    LoanType,
    LoanTypeLimit,
    NotifyPerson,
    NotifyType,
    NotifySubscription,
    Segment,
    Subscriber,
    IOUBlacklist,
)

from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith


audit_logger = logging.getLogger('AuditLogs')
audit_logger.setLevel(logging.INFO)

handler = logging.handlers.TimedRotatingFileHandler(
              AUDIT_LOGGING_PATH, 'midnight', 1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)

audit_logger.addHandler(handler)


class IouModelConverter(GeneralModelConverter):
    def __init__(self, datamodel, text_filter_col_mapping):
        super(IouModelConverter, self).__init__(datamodel)
        self.text_filter_col_mapping = text_filter_col_mapping

    def _convert_col(self, col_name,
                     label, description,
                     lst_validators, filter_rel_fields,
                     form_props):
        """
        Convert column into search field.
        Override parent class behavior to treat fields defined in text_filter_col_mapping as non relation field.
        """

        if self.text_filter_col_mapping and col_name in self.text_filter_col_mapping:
            mapped_col_name = self.text_filter_col_mapping[col_name]
            converted_column = super(IouModelConverter, self)._convert_simple(
                mapped_col_name,
                label,
                description,
                lst_validators,
                form_props
            )
            converted_column[col_name] = converted_column[mapped_col_name]
            return converted_column
        else:
            return super(IouModelConverter, self)._convert_col(col_name, label, description, lst_validators,
                                                        filter_rel_fields, form_props)


class IouModelView(SupersetModelView):
    """
    Dict storing column mappings for relation fields to avoid pre-loading all related values in select field,
    and instead use a text input field.
    Sample {"subscriber":"subscriber_id"}
    """
    text_filter_col_mapping = {}

    def to_json(self, inst):
        """
        Jsonify the sql alchemy query result.
        """
        convert = dict()
        d = dict()
        for c in inst.__table__.columns:
            v = getattr(inst, c.name)
            if c.type in convert.keys() and v is not None:
                try:
                    d[c.name] = convert[c.type](v)
                except:
                    d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
            elif v is None:
                d[c.name] = str()
            else:
                d[c.name] = v
        return json.dumps(d)

    def generate_request_id(self, original_id=''):
        new_id = uuid4()
        if original_id:
            new_id = "{},{}".format(original_id, new_id)
        return new_id

    def request_id(self):
        if getattr(g, 'request_id', None):
            return g.request_id

        headers = request.headers
        original_request_id = headers.get("X-Request-Id")
        new_uuid = self.generate_request_id(original_request_id)
        g.request_id = new_uuid

        return new_uuid

    def request_begin(self):
        g.request_begin = datetime.datetime.now().timestamp()

    def get_request_begin(self,):
        return g.request_begin

    def pre_operation(self, base_method, item):
        g.request_item = item
        base_method(item)

    def post_operation(self, base_method, item):
        base_method(item)
        g.response_item = item

    def pre_add(self, item):
        self.pre_operation(super(IouModelView, self).pre_add, item)

    def post_add(self, item):
        self.post_operation(super(IouModelView, self).post_add, item)

    def pre_update(self, item):
        self.pre_operation(super(IouModelView, self).pre_update, item)

    def post_update(self, item):
        self.post_operation(super(IouModelView, self).post_update, item)

    def pre_delete(self, item):
        self.pre_operation(super(IouModelView, self).pre_delete, item)

    def post_delete(self, item):
        self.post_operation(super(IouModelView, self).post_delete, item)

    def audit_log(self, request_id, start_ts, action, success, request_data, response_data):
        audit_logger.log(logging.INFO, '{}^|^{}^|^{}^|^{}^|^{}^|^{}^|^{}^|^{}^|^{}^|^{}^|^{}'.format(
            request_id,
            'IOU Core',
            request.host,
            start_ts,
            "",
            g.user.username,
            action,
            datetime.datetime.now().timestamp() - start_ts,
            success,
            request_data,
            response_data,
        ))

    def audit_action(self, base_method, operation, method, pk=None):
        if request.method == method:
            request_id = uuid4()
            start_ts = datetime.datetime.now().timestamp()
            success = False
            try:
                if pk:
                    resp = base_method(pk)
                else:
                    resp = base_method()
                success = True
                return resp
            finally:
                if hasattr(g, 'response_item'):
                    response_data = self.to_json(g.response_item)
                else:
                    response_data = json.dumps(self.datamodel.message)
                if isinstance(g.request_item, dict):
                    request_data = json.dumps(g.request_item)
                else:
                    request_data = self.to_json(g.request_item)
                self.audit_log(request_id, start_ts, operation, success, request_data, response_data)
        else:
            if pk:
                return base_method(pk)
            else:
                return base_method()

    def _add(self):
        return self.audit_action(super(IouModelView, self)._add, 'ADD', 'POST')

    def _edit(self, pk):
        return self.audit_action(super(IouModelView, self)._edit, 'EDIT', 'POST', pk)

    def _delete(self, pk):
        return self.audit_action(super(IouModelView, self)._delete, 'DELETE', 'GET', pk)

    def _init_titles(self):
        """
            Fix the Titles
        """
        if not self.list_title or self.list_title.startswith("List"):
            class_name = self.datamodel.model_name
            self.list_title = self._prettify_name(class_name)+'s'
        super(SupersetModelView, self)._init_titles()

    def _init_forms(self):
        """
            Init forms. Override parent behaviour to use text_filter_col_mapping to display text input for search form.
        """
        conv = IouModelConverter(self.datamodel, self.text_filter_col_mapping)
        if not self.search_form:
            self.search_form = conv.create_form(
                self.label_columns,
                self.search_columns,
                extra_fields=self.search_form_extra_fields,
                filter_rel_fields=self.search_form_query_rel_fields,
            )
        conv = GeneralModelConverter(self.datamodel)
        if not self.add_form:
            self.add_form = conv.create_form(
                self.label_columns,
                self.add_columns,
                self.description_columns,
                self.validators_columns,
                self.add_form_extra_fields,
                self.add_form_query_rel_fields,
            )
        if not self.edit_form:
            self.edit_form = conv.create_form(
                self.label_columns,
                self.edit_columns,
                self.description_columns,
                self.validators_columns,
                self.edit_form_extra_fields,
                self.edit_form_query_rel_fields,
            )


class FulfillmentActionTypeAttributeView(IouModelView):
    datamodel = SQLAInterface(FulfillmentActionTypeAttribute)
    edit_template = "appbuilder/general/model/edit_fulfillment_action_type_attribute.html"
    add_template = "appbuilder/general/model/add_fulfillment_action_type_attribute.html"

    add_form_extra_fields = edit_form_extra_fields = {
        'field_type': SelectField('Field Type',
                                  choices=[
                                      ('Number', 'Number'),
                                      ('String', 'String'),
                                      ('Date', 'Date'),
                                      ('Choice', 'Choice')],
                                  widget=Select2Widget()),
    }

    order_columns = ['attribute_name']
    base_order = ("fulfillment_action_type_id", "asc")

    list_columns = [
        'fulfillment_action_type', 'attribute_name', 'attribute_description', 'attribute_business_name',
        'field_type', 'default_value', 'send_to_fulfillment', 'allow_override']
    show_columns = add_columns = edit_columns = [
        'fulfillment_action_type', 'attribute_name', 'attribute_description', 'attribute_business_name',
        'default_value', 'send_to_fulfillment', 'allow_override','field_type', 'sf_min_length', 'sf_max_length', 
        'sf_validation_regex', 'sf_validation_error_msg','nf_min_value', 'nf_max_value', 'nf_num_decimals', 
        'nf_step', 'df_date_format', 'cf_choice_options']


    def validate_attribute_value(self, item):
        if item.field_type == 'Number':
            if item.nf_min_value > item.nf_max_value:
                raise Exception("Nf Min Value cannot be greater than Nf Max Value")
        elif item.field_type == 'String':
            if item.sf_min_length > item.sf_max_length:
                raise Exception("Sf Min Length cannot be greater than Sf Max Length")
        elif item.field_type == 'Date':
            try:
                datetime.datetime.now().strftime(item.df_date_format)
            except Exception as e:
                raise Exception("Invalid date format value {} value, valid examples: %d/%m/%y %H:%M:%S"
                                .format(item.df_date_format))
        elif item.field_type == 'Choice':
            if item.cf_choice_options.strip() == "":
                raise Exception("Invalid Cf Choice Options, values should be in format: option1,option2,option3")

    def pre_add(self, item):
        super(FulfillmentActionTypeAttributeView, self).pre_add(item)
        self.validate_attribute_value(item)

    def pre_update(self, item):
        super(FulfillmentActionTypeAttributeView, self).pre_update(item)
        self.validate_attribute_value(item)

    def post_add(self, item):
        super(FulfillmentActionTypeAttributeView, self).post_add(item)
        actions = db.session.query(FulfillmentAction)\
            .filter_by(fulfillment_action_type_id=item.fulfillment_action_type_id).all()
        for action in actions:
            action_value = FulfillmentActionValue()
            action_value.fulfillment_action_id = action.fulfillment_action_id
            action_value.fulfillment_action_attr_name = item.attribute_name
            action_value.value = item.default_value
            db.session.add(action_value)
        db.session.commit()

    def post_delete(self, item):
        super(FulfillmentActionTypeAttributeView, self).post_delete(item)
        actions = db.session.query(FulfillmentAction)\
            .filter_by(fulfillment_action_type_id=item.fulfillment_action_type_id).all()
        for action in actions:
            action_values = db.session.query(FulfillmentActionValue)\
                .filter_by(fulfillment_action_id=action.fulfillment_action_id,
                           fulfillment_action_attr_name=item.attribute_name)
            for action_value in action_values:
                db.session.delete(action_value)
        db.session.commit()


class FulfillmentActionTypeView(IouModelView):
    datamodel = SQLAInterface(FulfillmentActionType)

    show_template = "appbuilder/general/model/show_cascade_expanded.html"
    edit_template = "appbuilder/general/model/edit_cascade_expanded.html"

    list_columns = ['name', 'description']
    order_columns = ['name']
    base_order = ("fulfillment_action_type_id", "asc")
    related_views = [FulfillmentActionTypeAttributeView]


class FulfillmentActionValueView(IouModelView):
    datamodel = SQLAInterface(FulfillmentActionValue)

    def validate_action_value(self, item):
        faa = item.fulfillment_action_attribute
        if faa.field_type == 'Number':
            if faa.nf_min_value > float(item.value) or faa.nf_max_value < float(item.value):
                raise Exception("{} value should be between {} and {}"
                                .format(faa.attribute_name, faa.nf_min_value, faa.nf_max_value))
            item.value = str(round(float(item.value), faa.nf_num_decimals))
        elif faa.field_type == 'String':
            if faa.sf_min_length > len(item.value) or faa.sf_max_length < len(item.value):
                raise Exception("{} length should be between {} and {} characters"
                                .format(faa.attribute_name, faa.sf_min_length, faa.sf_max_length))
            if not re.match(faa.sf_validation_regex, item.value):
                raise Exception(faa.sf_validation_error_msg)
        elif faa.field_type == 'Date':
            try:
                datetime.datetime.strptime(item.value, faa.df_date_format)
            except Exception as e:
                raise Exception("{} value has invalid date format {}, format should be {}"
                                .format(faa.attribute_name, item.value, faa.df_date_format))
        elif faa.field_type == 'Choice':
            if faa.cf_choice_options and faa.cf_choice_options != "":
                values = faa.cf_choice_options.split(",")
                if item.value not in values:
                    raise Exception("{} has invalid value {}, value should be one of {}"
                                .format(faa.attribute_name, item.value, faa.cf_choice_options))


    def pre_add(self, item):
        super(FulfillmentActionValueView, self).pre_add(item)
        self.validate_action_value(item)

    def pre_update(self, item):
        super(FulfillmentActionValueView, self).pre_update(item)
        self.validate_action_value(item)

    list_columns = ['fulfillment_action_attribute', 'value']
    order_columns = ['fulfillment_action_attribute']
    base_order = ("fulfillment_action_id", "asc")

class FulfillmentActionView(IouModelView):
    datamodel = SQLAInterface(FulfillmentAction)

    show_template = "appbuilder/general/model/show_cascade_expanded.html"
    edit_template = "appbuilder/general/model/edit_cascade_expanded.html"

    show_columns = list_columns = add_columns = edit_columns = ['name', 'description', 'fulfillment_action_type']

    order_columns = ['name']
    base_order = ("fulfillment_action_id", "asc")

    related_views = [FulfillmentActionValueView]

    def post_add(self, item):
        super(FulfillmentActionView, self).post_add(item)
        attributes = db.session.query(FulfillmentActionTypeAttribute)\
            .filter_by(fulfillment_action_type_id=item.fulfillment_action_type_id).all()
        for attribute in attributes:
            action_value = FulfillmentActionValue()
            action_value.fulfillment_action_attr_name = attribute.attribute_name
            action_value.fulfillment_action_id = item.fulfillment_action_id
            action_value.value = attribute.default_value
            db.session.add(action_value)
        db.session.commit()



class LoanTransactionView(IouModelView):
    datamodel = SQLAInterface(LoanTransaction)

    list_columns = [
        'loan_transaction_type', 'subscriber', 'amount','cdmainid', 'transaction_dt', 'transaction_data',
        'reason', 'last_updated_dt', 'repay_to_currency_rate']

    show_columns = [
        'loan_transaction_type', 'subscriber', 'amount', 'cdmainid', 'transaction_dt', 'transaction_data',
        'reason', 'foreign_transaction_ref_id', 'foreign_transaction_dt', 'last_updated_dt', 'repay_to_currency_rate']

    search_exclude_columns = ['loan']

    order_columns = ['transaction_dt','loan_transaction_type','subscriber']
    base_order = ("last_updated_dt", "asc")

    text_filter_col_mapping = {'subscriber': 'subscriber_id'}


class OutstandingLoanView(IouModelView):
    datamodel = SQLAInterface(Loan)

    base_filters = [['outstanding_amount', FilterGreater, 0],['status',FilterNotEqual,'Loan Failed']]

    list_title = 'Outstanding Loans'

    list_columns = show_columns = [
        'subscriber', 'loan_type', 'offer_channel', 'trigger_channel', 'principal_amount', 'origination_fee','cdmainid',
        'origination_reason', 'origination_dt', 'outstanding_amount', 'outstanding_fee', 'status','repay_to_currency_rate', 
        'repayment_dt', 'last_payment', 'last_payment_dt', 'last_fee_payment', 'last_fee_payment_dt',
        'last_updated_dt'
    ]
    order_columns = ['origination_dt','subscriber']
    base_order = ("origination_dt", "desc")
    related_views = [LoanTransactionView]


class LoanView(IouModelView):
    datamodel = SQLAInterface(Loan)

    list_columns = show_columns = [
        'subscriber', 'loan_type', 'offer_channel', 'trigger_channel', 'principal_amount', 'origination_fee','cdmainid',
        'origination_reason', 'origination_dt', 'outstanding_amount', 'outstanding_fee', 'status','repay_to_currency_rate', 
        'repayment_dt', 'last_payment', 'last_payment_dt', 'last_fee_payment', 'last_fee_payment_dt',
        'last_updated_dt'
    ]

    search_exclude_columns = ['transactions']
    order_columns = ['origination_dt','subscriber']
    base_order = ("origination_dt", "desc")
    related_views = [LoanTransactionView]

    text_filter_col_mapping = {'subscriber': 'subscriber_id'}


class LoanChannelView(IouModelView):
    datamodel = SQLAInterface(LoanChannel)

    list_columns = show_columns = ['name', 'type', 'last_updated_dt', 'last_updated_by']
    add_columns = edit_columns = ['name', 'type']
    order_columns = ['name']
    base_order = ("channel_id", "asc")


class LoanTransactionTypeView(IouModelView):
    datamodel = SQLAInterface(LoanTransactionType)

    list_columns = show_columns = ['name', 'description', 'last_updated_dt', 'last_updated_by']
    add_columns = edit_columns = ['name', 'description']


class LoanTypeView(IouModelView):
    datamodel = SQLAInterface(LoanType)

    list_columns = show_columns = [
        'name', 'description', 'product_id', 'principal_type', 'repayment_type', 'borrow_loan_action',
        'repay_loan_action', 'repay_to_currency_rate', 'last_updated_dt', 'last_updated_by'
    ]
    add_columns = edit_columns = [
        'name', 'description', 'product_id', 'principal_type', 'repayment_type', 'borrow_loan_action',
        'repay_loan_action', 'repay_to_currency_rate'
    ]
    search_columns = [
        'name', 'description', 'product_id', 'principal_type', 'repayment_type', 'borrow_loan_action',
        'repay_loan_action', 'repay_to_currency_rate'
    ]
    order_columns = ['name']
    base_order = ("loan_type_id", "asc")

class LoanTypeLimitView(IouModelView):
    datamodel = SQLAInterface(LoanTypeLimit)

    list_columns = show_columns = [
        'loan_type', 'loan_limit_amount', 'current_loan_exposure', 'alert_threshold', 'alert_step_up', 
        'minimum_remaining_balance', 'last_updated_dt', 'last_updated_by'
    ]
    add_columns = [
        'loan_type', 'loan_limit_amount', 'current_loan_exposure', 'alert_threshold', 'alert_step_up', 'minimum_remaining_balance'
    ]
    edit_columns = [
        'loan_type', 'loan_limit_amount', 'alert_threshold', 'alert_step_up', 'minimum_remaining_balance'
    ]

    add_form_extra_fields = {
        'loan_limit_amount': StringField('Loan Type Limit', widget=BS3TextFieldWidget(), default=0),
        'current_loan_exposure': StringField('Current Loan Exposure', widget=BS3TextFieldWidget(), default=0),
        'alert_threshold': StringField('Alert Threshold', widget=BS3TextFieldWidget(), default=80),
        'alert_step_up': StringField('Alert Step Up', widget=BS3TextFieldWidget(), default=5),
        'minimum_remaining_balance': StringField('Minimum Remaining Balance', widget=BS3TextFieldWidget(), default=0),
    }

    edit_form_extra_fields = {
        'loan_limit_amount': StringField('Loan Type Limit', widget=BS3TextFieldWidget(), default=0),
        'alert_threshold': StringField('Alert Threshold', widget=BS3TextFieldWidget(), default=80),
        'alert_step_up': StringField('Alert Step Up', widget=BS3TextFieldWidget(), default=5),
        'minimum_remaining_balance': StringField('Minimum Remaining Balance', widget=BS3TextFieldWidget(), default=0),
    }

    order_columns = ['loan_type']

    def pre_add(self, item):
        super(LoanTypeLimitView, self).pre_add(item)
        company_brand_arg = list(filter(lambda x: (x.endswith('company_brand')), request.args.keys()))
        if len(company_brand_arg) > 0:
            item.id_source = 'company_brand'
            item.source_id = request.args[company_brand_arg[0]]
        else:
            subscriber_arg = list(filter(lambda x: (x.endswith('subscriber')), request.args.keys()))
            if len(subscriber_arg) > 0:
                item.id_source = 'subscriber'
                item.source_id = request.args[subscriber_arg[0]]
            else:
                segment_arg = list(filter(lambda x: (x.endswith('segment')), request.args.keys()))
                if len(segment_arg) > 0:
                    item.id_source = 'segment'
                    item.source_id = request.args[segment_arg[0]]

        item.next_alert_threshold = item.alert_threshold



class CompanyBrandView(IouModelView):
    datamodel = SQLAInterface(CompanyBrand)

    list_columns = ['name', 'description']
    add_exclude_columns = edit_exclude_columns = show_exclude_columns = ['loan_limits']
    search_columns = ['name', 'description']

    order_columns = ['name']
    base_order = ("company_brand_id", "asc")
    related_views = [LoanTypeLimitView]


class NotifyTypeView(IouModelView):
    datamodel = SQLAInterface(NotifyType)

    list_columns = ['name', 'description']


class NotifySubscriptionView(IouModelView):
    datamodel = SQLAInterface(NotifySubscription)

    list_columns = show_columns = add_columns = edit_columns = ['notify_type','person','channel']
    # edit_exclude_columns = ['last_updated_dt', 'last_updated_by']
    order_columns = ['notify_type']
    base_order = ("notify_type_id", "asc")

class NotifyPersonView(IouModelView):
    datamodel = SQLAInterface(NotifyPerson)

    list_columns = ['name', 'description', 'msisdn', 'email_address']
    # edit_exclude_columns = ['last_updated_dt', 'last_updated_by']

    related_views = [NotifySubscriptionView]
    order_columns = ['name']
    base_order = ("person_id", "asc")

class SegmentView(IouModelView):
    datamodel = SQLAInterface(Segment)

    list_columns = show_columns = add_columns = edit_columns = ['name', 'description']
    # edit_exclude_columns = ['loan_limits', 'last_updated_dt', 'last_updated_by']

    related_views = [LoanTypeLimitView]


class SubscriberView(IouModelView):
    datamodel = SQLAInterface(Subscriber)

    base_order = ('subscriber_id','asc')

    search_columns = ['msisdn', 'subscriber_id', 'company_brand', 'loans_disabled']

    list_columns = show_columns = [
        'subscriber_id', 'msisdn', 'company_brand', 'loans_disabled', 'last_seen_dt', 'first_seen_dt'
    ]
    edit_columns = [
        'subscriber_id', 'company_brand', 'msisdn', 'loans_disabled', 'last_seen_dt', 'first_seen_dt'
    ]

    edit_form_extra_fields = {
        'subscriber_id': StringField('Subscriber Id', widget=BS3TextFieldROWidget()),
        'msisdn': StringField('Msisdn', widget=BS3TextFieldROWidget()),
        'company_brand':  StringField('Company Brand', widget=BS3TextFieldROWidget()),
        'last_seen_dt': StringField('Last Seen Dt', widget=BS3TextFieldROWidget()),
        'first_seen_dt': StringField('First Seen Dt', widget=BS3TextFieldROWidget()),
    }

    related_views = [LoanTypeLimitView, OutstandingLoanView, LoanView, LoanTransactionView]

class IOUBlacklistView(IouModelView):
    datamodel = SQLAInterface(IOUBlacklist)

    list_columns = show_columns = ['subscriber_id','optd_out','note','last_updated_dt']

    add_columns = ['subscriber_id','optd_out','note']
    edit_columns = ['subscriber_id','optd_out','note']

    edit_form_extra_fields = {
        'subscriber_id': StringField('Subscriber Id', widget=BS3TextFieldROWidget())
    }

    search_columns = ['subscriber_id']

    order_columns = ['subscriber_id','last_updated_dt']

    base_order = ("last_updated_dt", "desc")
