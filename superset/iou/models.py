
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import get_history

from superset import db
from sqlalchemy.ext.declarative import declared_attr
from flask import g, json
from sqlalchemy import event, inspect
import datetime
import logging
import pytz
import enum


# class IouUserMixin(object):
#
#     @classmethod
#     def get_user_name(cls):
#         try:
#             return g.user.username
#         except Exception:
#             return None
#
#     @declared_attr
#     def last_updated_dt(cls):
#         return db.Column(db.Integer, default=datetime.datetime.now, onupdate=datetime.datetime.now, nullable=False)
#
#     @declared_attr
#     def last_updated_by(cls):
#         return db.Column(db.Integer, default=cls.get_user_name, onupdate=cls.get_user_name, nullable=False

class AuditableMixin:
    """Allow a model to be automatically audited"""
    ACTION_UPDATE = 'UPDATE'

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'after_update', cls.audit_update)

    @staticmethod
    def audit_update(mapper, connection, target):
        try:
            state_before = {}
            state_after = {}
            inspr = inspect(target)
            attrs = class_mapper(target.__class__).column_attrs
            for attr in attrs:
                hist = getattr(inspr.attrs, attr.key).history
                if hist.has_changes():
                    state_before[attr.key] = get_history(target, attr.key)[2].pop()
                    state_after[attr.key] = getattr(target, attr.key)

            g.request_item = {"before" : state_before, "after": state_after}

        except Exception as e:
            logging.warning("Failed create audit log for an update action", e)


class FulfillmentAction(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'fulfillment_action'

    fulfillment_action_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    fulfillment_action_type_id = db.Column(db.Integer,
                                           db.ForeignKey('fulfillment_action_type.fulfillment_action_type_id'),
                                           nullable=False)
    fulfillment_action_type = db.relationship("FulfillmentActionType", foreign_keys=[fulfillment_action_type_id])

    def __repr__(self):
        return self.name


class FulfillmentActionType(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'fulfillment_action_type'

    fulfillment_action_type_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


class FulfillmentActionTypeAttribute(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'fulfillment_action_type_attrs'

    fulfillment_action_type_id = db.Column(db.Integer,
                                           db.ForeignKey('fulfillment_action_type.fulfillment_action_type_id'),
                                           primary_key=True, nullable=False)
    fulfillment_action_type = db.relationship("FulfillmentActionType", foreign_keys=[fulfillment_action_type_id])
    attribute_name = db.Column(db.String(255), primary_key=True, nullable=False)
    attribute_description = db.Column(db.String(255), nullable=False)
    attribute_business_name = db.Column(db.String(255), nullable=False)
    default_value = db.Column(db.String(255), nullable=False)
    send_to_fulfillment = db.Column(db.Boolean)
    allow_override = db.Column(db.Boolean)
    field_type = db.Column(db.String(255), nullable=False)
    sf_min_length = db.Column(db.Integer)
    sf_max_length = db.Column(db.Integer)
    sf_validation_regex = db.Column(db.String(255))
    sf_validation_error_msg = db.Column(db.String(255))
    nf_min_value = db.Column(db.Numeric)
    nf_max_value = db.Column(db.Numeric)
    nf_num_decimals = db.Column(db.Integer)
    nf_step = db.Column(db.Integer)
    df_date_format = db.Column(db.String(255))
    cf_choice_options = db.Column(db.String(255))
    

    def __repr__(self):
        return self.attribute_name


class FulfillmentActionValue(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'fulfillment_action_values'

    fulfillment_action_id = db.Column(db.Integer, db.ForeignKey('fulfillment_action.fulfillment_action_id'),
                                      primary_key=True, nullable=False)
    fulfillment_action = db.relationship("FulfillmentAction", foreign_keys=[fulfillment_action_id])

    fulfillment_action_attr_name = db.Column(db.String(255),
                                             db.ForeignKey('fulfillment_action_type_attrs.attribute_name'),
                                             primary_key=True, nullable=False)
    fulfillment_action_attribute = db.relationship("FulfillmentActionTypeAttribute",
                                              foreign_keys=[fulfillment_action_attr_name])
    value = db.Column(db.String(255), nullable=False)


class LoanChannel(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'channel'

    channel_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)

    last_updated_dt = db.Column(db.DateTime, nullable=False, server_default=db.func.sysdate())
    last_updated_by = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


class Loan(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'loan'

    loan_id = db.Column(db.Integer, primary_key=True)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.subscriber_id'), nullable=False)
    subscriber = db.relationship("Subscriber", foreign_keys=[subscriber_id], backref='loan_history')

    loan_type_id = db.Column(db.Integer, db.ForeignKey('loan_type.loan_type_id'), nullable=False)
    loan_type = db.relationship("LoanType", foreign_keys=[loan_type_id])

    offer_channel_id = db.Column(db.Integer, db.ForeignKey('channel.channel_id'), nullable=False)
    offer_channel = db.relationship("LoanChannel", foreign_keys=[offer_channel_id])

    trigger_channel_id = db.Column(db.Integer, db.ForeignKey('channel.channel_id'), nullable=False)
    trigger_channel = db.relationship("LoanChannel", foreign_keys=[trigger_channel_id])

    principal_amount = db.Column(db.Numeric, nullable=False)
    origination_fee = db.Column(db.Numeric, nullable=False)
    cdmainid = db.Column(db.String(255), nullable=True)
    origination_reason = db.Column(db.String(255), nullable=False)
    origination_dt = db.Column(db.DateTime, nullable=False)

    repay_to_currency_rate = db.Column(db.Numeric, nullable=False)
    outstanding_amount = db.Column(db.Numeric, nullable=False)
    outstanding_fee = db.Column(db.Numeric, nullable=False)
    repayment_dt = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(255), nullable=False)
    last_payment = db.Column(db.Numeric, nullable=False)
    last_payment_dt = db.Column(db.DateTime, nullable=False)
    last_fee_payment = db.Column(db.Numeric, nullable=False)
    last_fee_payment_dt = db.Column(db.DateTime, nullable=False)
    last_updated_dt = db.Column(db.DateTime, nullable=False)


class LoanTransaction(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'loan_transaction'

    transaction_id = db.Column(db.Integer, primary_key=True)

    loan_transaction_type_id = db.Column(db.Integer, db.ForeignKey('loan_transaction_type.loan_transaction_type_id'),
                                         nullable=False)
    loan_transaction_type = db.relationship("LoanTransactionType", foreign_keys=[loan_transaction_type_id],
                                            backref='transactions')

    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscriber.subscriber_id'), nullable=False)
    subscriber = db.relationship("Subscriber", foreign_keys=[subscriber_id], backref='loan_transactions')

    loan_id = db.Column(db.Integer, db.ForeignKey('loan.loan_id'), nullable=False)
    loan = db.relationship("Loan", foreign_keys=[loan_id], backref='transactions')

    amount = db.Column(db.Numeric, nullable=False)
    repay_to_currency_rate = db.Column(db.Numeric, nullable=True)
    cdmainid = db.Column(db.String(255), nullable=True)

    transaction_dt = db.Column(db.DateTime, nullable=False)
    transaction_data = db.Column(db.String, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    foreign_transaction_ref_id = db.Column(db.String(255), nullable=False)
    foreign_transaction_dt = db.Column(db.DateTime, nullable=False)
    last_updated_dt = db.Column(db.DateTime, nullable=False)


class LoanTransactionType(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'loan_transaction_type'

    loan_transaction_type_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    last_updated_dt = db.Column(db.DateTime, nullable=False, server_default=db.func.sysdate())
    last_updated_by = db.Column(db.String, nullable=False)

    def __repr__(self):
        return self.name


class LoanType(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'loan_type'

    loan_type_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.String(255), nullable=False)
    principal_type = db.Column(db.String(255), nullable=False)
    repayment_type = db.Column(db.String(255), nullable=False)
    borrow_loan_action_id = db.Column(db.Integer, nullable=False)
    repay_loan_action_id = db.Column(db.Integer, nullable=False)

    repay_to_currency_rate = db.Column(db.Numeric, nullable=True)
    last_updated_dt = db.Column(db.DateTime, nullable=False, server_default=db.func.sysdate())
    last_updated_by = db.Column(db.DateTime, nullable=False)

    borrow_loan_action = db.relationship(
        "FulfillmentAction",
        primaryjoin="and_(LoanType.borrow_loan_action_id == FulfillmentAction.fulfillment_action_id, "
                    "FulfillmentAction.fulfillment_action_type_id == FulfillmentActionType.fulfillment_action_type_id)",
        foreign_keys=[borrow_loan_action_id, principal_type])

    repay_loan_action = db.relationship(
        "FulfillmentAction",
        primaryjoin="and_(LoanType.repay_loan_action_id == FulfillmentAction.fulfillment_action_id, "
                    "FulfillmentAction.fulfillment_action_type_id == FulfillmentActionType.fulfillment_action_type_id)",
        foreign_keys=[repay_loan_action_id, repayment_type])

    def __repr__(self):
        return self.name


class LoanTypeLimit(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'loan_type_limits'

    id_source = db.Column(db.String(255), primary_key=True, nullable=False)
    source_id = db.Column(db.Integer, primary_key=True, nullable=False)
    loan_type_id = db.Column(db.Integer, db.ForeignKey('loan_type.loan_type_id'), primary_key=True, nullable=False)
    loan_type = db.relationship("LoanType", foreign_keys=[loan_type_id])

    loan_limit_amount = db.Column(db.Numeric, nullable=False)
    current_loan_exposure = db.Column(db.Numeric, nullable=False)
    alert_threshold = db.Column(db.Numeric, nullable=False)
    minimum_remaining_balance = db.Column(db.Numeric, nullable=False)
    last_updated_dt = db.Column(db.DateTime, nullable=False, server_default=db.func.sysdate())
    last_updated_by = db.Column(db.String(255), nullable=False)
    next_alert_threshold = db.Column(db.Numeric, nullable=False)
    alert_step_up = db.Column(db.Numeric, nullable=False, default=5)

    company_brand = db.relationship("CompanyBrand",
                                    primaryjoin='and_(CompanyBrand.company_brand_id == LoanTypeLimit.source_id, '
                                                'LoanTypeLimit.id_source == "company_brand")', foreign_keys=[source_id],
                                    backref='loan_limits')

    segment = db.relationship("Segment",
                              primaryjoin='and_(Segment.segment_id == LoanTypeLimit.source_id, '
                                          'LoanTypeLimit.id_source == "segment")', foreign_keys=[source_id],
                              backref='loan_limits')

    subscriber = db.relationship("Subscriber",
                                 primaryjoin='and_(Subscriber.subscriber_id == LoanTypeLimit.source_id, '
                                             'LoanTypeLimit.id_source == "subscriber")', foreign_keys=[source_id],
                                 backref='loan_limits')


class CompanyBrand(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'company_brand'

    company_brand_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


class NotifyPerson(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'notify_person'

    person_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)
    msisdn = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


class NotifySubscription(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'notify_subscription'

    notify_type_id = db.Column(db.Integer, db.ForeignKey('notify_type.notify_type_id'), primary_key=True,
                               nullable=False)
    notify_type = db.relationship("NotifyType", foreign_keys=[notify_type_id])

    person_id = db.Column(db.Integer, db.ForeignKey('notify_person.person_id'), primary_key=True, nullable=False)
    person = db.relationship("NotifyPerson", foreign_keys=[person_id])
    channel = db.Column(db.String(255), primary_key=True, nullable=False)


class NotifyType(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'notify_type'

    notify_type_id = db.Column(db.Integer, primary_key=True, server_default=db.func.sysdate())
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


t_segment_membership = db.Table(
    'segment_membership', db.metadata,
    db.Column('segment_id', db.Integer, db.ForeignKey('segment.segment_id'), primary_key=True, nullable=False),
    db.Column('subscriber_id', db.Integer, db.ForeignKey('subscriber.subscriber_id'), primary_key=True, nullable=False),
    info={'bind_key': 'iou'}
)


class Segment(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'segment'

    segment_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    subscribers = db.relationship("Subscriber", secondary=t_segment_membership, back_populates="segments")

    def __repr__(self):
        return self.name


class Subscriber(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'subscriber'

    subscriber_id = db.Column(db.Integer, primary_key=True)
    msisdn = db.Column(db.String(255), nullable=False)

    company_brand_id = db.Column(db.Integer, db.ForeignKey('company_brand.company_brand_id'), nullable=False)
    company_brand = db.relationship("CompanyBrand", foreign_keys=[company_brand_id])

    last_seen_dt = db.Column(db.DateTime, nullable=False)
    first_seen_dt = db.Column(db.DateTime, nullable=False)
    loans_disabled = db.Column(db.Boolean)
    # credit_score = db.Column(db.Numeric, nullable=False)
    # churn_score = db.Column(db.Numeric, nullable=False)
    # nps_score = db.Column(db.Numeric, nullable=False)

    segments = db.relationship("Segment", secondary=t_segment_membership, back_populates="subscribers")

    def __repr__(self):
        return str(self.subscriber_id)

    # Make a readonly company brand field
    @hybrid_property
    def company_brand_ro(self):
        return self.company_brand.name

    # Readonly company brand field setter
    @company_brand_ro.setter
    def company_brand_ro(self, val):
        pass

#To ADD dropdow for opted_out / blacklisted
class DropdownBoolean(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'iou_drpdwn_flds'

    id = db.Column(db.Integer,primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return str(self.value)

class IOUBlacklist(db.Model, AuditableMixin):
    __bind_key__ = 'iou'
    __tablename__ = 'iou_blacklist'
    #__tablename__ = 'iou_blacklist_cp'

    subscriber_id = db.Column(db.Integer,primary_key=True)
    last_updated_dt = db.Column(db.DateTime, nullable=False, server_default=db.func.sysdate())
    opted_out = db.Column(db.Integer,db.ForeignKey('iou_drpdwn_flds.id'), nullable=False)
    note = db.Column(db.String(255), nullable=False)

    blacklisted = db.relationship("DropdownBoolean",
                  #  primaryjoin="and_(DropdownBoolean.id == IOUBlacklist.opted_out)",
                    foreign_keys=[opted_out])

    def __repr__(self):
        return str(self.subscriber_id)

def model_before_save(mapper, connection, target):
    timezone = pytz.timezone("Asia/Jakarta")
    target.last_updated_dt = datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    try:
        target.last_updated_by = g.user.username
    except Exception:
        target.last_updated_by = 'Unknown'



for model in [LoanChannel, LoanTransactionType, LoanType, LoanTypeLimit, IOUBlacklist]:
    @event.listens_for(model, 'before_insert')
    def model_before_insert(mapper, connection, target):
        print("inside before insert")
        model_before_save(mapper, connection, target)

    @event.listens_for(model, 'before_update')
    def model_before_update(mapper, connection, target):
        print("inside before update")
        model_before_save(mapper, connection, target)