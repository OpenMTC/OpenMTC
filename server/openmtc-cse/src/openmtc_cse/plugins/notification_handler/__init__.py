from openmtc_onem2m import OneM2MRequest
from openmtc_onem2m.exc import CSENotFound
from openmtc_onem2m.model import (
    Subscription,
    Notification,
    SubscribableResource,
    NotificationEventC,
    NotificationContentTypeE,
    EventNotificationCriteria,
    NotificationEventTypeE,
    AggregatedNotification,
)
from openmtc_onem2m.transport import OneM2MOperation
from openmtc_server.Plugin import Plugin

import datetime


def get_event_notification_criteria(subscription):
    # If the eventNotificationCriteria attribute is set, then the Originator
    # shall check whether the corresponding event matches with the event
    # criteria.
    event_notification_criteria = subscription.eventNotificationCriteria \
                                  or EventNotificationCriteria()
    # If the eventNotificationCriteria attribute is not configured, the
    # Originator shall use the default setting of Update_of_Resource for
    # notificationEventType and then continue with the step 2.0

    # If notificationEventType is not set within the eventNotificationCriteria
    # attribute, the Originator shall use the default setting of
    # Update_of_Resource to compare against the event.
    if not event_notification_criteria.notificationEventType:
        event_notification_criteria.notificationEventType = [NotificationEventTypeE.updateOfResource]

    # If the event matches, go to the step 2.0. Otherwise, the Originator shall
    # discard the corresponding event
    return event_notification_criteria


class NotificationHandler(Plugin):
    def __init__(self, api, config, *args, **kw):
        super(NotificationHandler, self).__init__(api, config, *args,  **kw)

        # subscriptions_info contains the relevant info of a current
        # subscriptions, i.e. {pid: {rid: {net: value, ...}}}
        self.subscriptions_info = {}
        cse_id = config.get('onem2m', {}).get('cse_id', 'mn-cse-1')
        sp_id = config.get('onem2m', {}).get('sp_id', 'openmtc.org')
        self._rel_cse_id = '/' + cse_id
        self._abs_cse_id = '//' + sp_id + '/' + cse_id

    def _init(self):
        # subscription created
        self.events.resource_created.register_handler(self._handle_subscription_created, Subscription)

        # subscription updated
        self.events.resource_updated.register_handler(self._handle_subscription_updated, Subscription)

        # subscription deleted
        self.events.resource_deleted.register_handler(self._handle_subscription_deleted, Subscription)

        # resource updated
        self.events.resource_updated.register_handler(self._handle_subscribable_resource_updated, SubscribableResource)

        # resource created
        self.events.resource_created.register_handler(self._handle_subscribable_resource_created, SubscribableResource)

        # resource deleted
        self.events.resource_deleted.register_handler(self._handle_subscribable_resource_deleted, SubscribableResource)

        self._initialized()

    def _get_sub_list(self, pid, net):
        return [
            v['sub'] for v in self.subscriptions_info.itervalues()
            if v['pid'] == pid and net in v['enc'].notificationEventType
        ]

    def _delete_subs_from_parent(self, pid):
        self.subscriptions_info = {
            k: v for k, v in self.subscriptions_info.iteritems() if v["pid"] != pid
        }

    def _handle_subscription_created(self, subscription, _):
        # todo: store somewhere
        # if not self.subscriptions_info.get(subscription.resourceID):
        #     self.subscriptions_info[subscription.resourceID] = {}

        self.subscriptions_info[subscription.resourceID] = {
            "pid": subscription.parentID,
            "enc": get_event_notification_criteria(subscription),
            "sub": subscription,
            "not": [],                      # notifications
            "levt": datetime.datetime.now() # last event time
        }

    def _handle_subscription_updated(self, subscription, _):
        self.subscriptions_info[subscription.resourceID].update({
            "enc": get_event_notification_criteria(subscription),
            # TODO(rst): test this
            "sub": subscription,
        })

    def _handle_subscription_deleted(self, subscription, req):
        # only when subscription is deleted directly
        if not req.cascading:
            try:
                del self.subscriptions_info[subscription.resourceID]
            except KeyError:
                pass

        # 7.5.1.2.4 Notification for Subscription Deletion
        # Originator:
        # When the <subscription> resource is deleted and subscriberURI of the
        # <subscription> resource is configured, the Originator shall send a
        # Notify request primitive with subscriptionDeletion element of the
        # notification data object set as TRUE and subscriptionReference element
        # set as the URI of the <subscription> resource to the entity indicated
        # in subscriberURI.

        su = subscription.subscriberURI
        if not su:
            return

        try:
            self.api.handle_onem2m_request(OneM2MRequest(
                OneM2MOperation.notify,
                su,
                pc=Notification(
                    subscriptionDeletion=True,
                    subscriptionReference=subscription.path,
                ),
            ))
        except CSENotFound:
            self.logger.debug("subscription target %s already deleted or not existing." % su)

    def _handle_subscribable_resource_updated(self, resource, _):
        self.logger.debug("_handle_subscribable_resource_updated for %s", resource)

        map(
            lambda sub: self._handle_subscription(resource, sub),
            self._get_sub_list(
                resource.resourceID,
                NotificationEventTypeE.updateOfResource,
            )
        )

    def _handle_subscribable_resource_created(self, resource, _):
        self.logger.debug("_handle_subscribable_resource_created for %s", resource)

        map(
            lambda sub: self._handle_subscription(resource, sub),
            self._get_sub_list(
                resource.parentID,
                NotificationEventTypeE.createOfDirectChildResource,
            )
        )

    def _handle_subscribable_resource_deleted(self, resource, _):
        self.logger.debug("_handle_subscribable_resource_deleted for %s", resource)

        rid = resource.resourceID
        net_delete = NotificationEventTypeE.deleteOfResource
        pid = resource.parentID
        net_delete_child = NotificationEventTypeE.deleteOfDirectChildResource

        sub_list = (self._get_sub_list(rid, net_delete) + self._get_sub_list(pid, net_delete_child))

        for sub in sub_list:
            self._handle_subscription(resource, sub)

        # delete remaining subscriptions of parent from subscriptions_info
        self._delete_subs_from_parent(resource.resourceID)

    def _handle_subscription(self, resource, sub):
        self.logger.debug("_handle_subscription: %s", sub.get_values())

        # 7.5.1.2.2 Notification for modification of subscribed resources
        # When the notification message is forwarded or aggregated by transit
        # CSEs, the Originator or a transit CSE shall check whether there are
        # notification policies to enforce between subscription resource Hosting
        # CSE and the notification target. In that case, the transit CSE as well
        # as the Originator shall process Notify request primitive(s) by using
        # the corresponding policy and send processed Notify request
        # primitive(s) to the next CSE with notification policies related to the
        # enforcement so that the transit CSE is able to enforce the policy
        # defined by the subscriber. The notification policies related to the
        # enforcement at this time is verified by using the subscription
        # reference in the Notify request primitive. In the notification
        # policies, the latestNotify attribute is only enforced in the transit
        # CSE as well as the Originator.

        # If Event Category parameter is set to ''latest' in the notification
        # request primitive, the transit CSE as well as Originator shall cache
        # the most recent Notify request. That is, if a new Notify request is
        # received by the CSE with a subscription reference that has already
        # been buffered for a pending Notify request, the newer Notify request
        # will replace the buffered older Notify request.

        # Originator: When an event is generated, the Originator shall execute
        # the following steps in order:

        # Step 1.0 Check the eventNotificationCriteria attribute of the
        # <subscription> resource associated with the modified resource:

        def __check_event_notification_criteria():
            # return check_match()
            return True

        if not __check_event_notification_criteria():
            return

        # step 2.0
        # The Originator shall check the notification policy as described in the
        # below steps, but the notification policy may be checked in different
        # order. After checking the notification policy in step 2.0 (i.e., from
        # step 2.1to step 2.6), then continue with step 3.0

        # Step 2.1 The Originator shall determine the type of the notification
        # per the notificationContentType attribute. The possible values of for
        # notificationContentType attribute are 'Modified Attributes', 'All
        # Attributes', and or optionally 'ResourceID'. This attribute may be
        # used joint with eventType attribute in the eventNotificationCriteria
        # to determine if it is the attributes of the subscribed-to resource or
        # the attributes of the child resource of the subscribed-to resource
        # that shall be returned in the notification.
        notification_content_type = sub.notificationContentType or NotificationContentTypeE.allAttributes

        # - If the value of notificationContentType is set to 'All Attributes',
        #   the Notify request primitive shall include the whole subscribed-to
        #   resource
        # - If the notificationContentType attribute is not configured, the
        #   default value is set to 'All Attributes'
        # - If the value of notificationContentType is set to 'Modified
        #   Attribute', the Notify request primitive shall include the modified
        #   attribute(s) only
        # - If the value of notificationContentType is set to 'ResourceID', the
        #   Notify request primitive shall include the resourceID of the
        #   subscribed-to resource
        if notification_content_type is (
                    NotificationContentTypeE.allAttributes,
                    NotificationContentTypeE.modifiedAttributes,
                    NotificationContentTypeE.resourceID,
                ):
            pass

        # Step 2.2 Check the notificationEventCat attribute:
        try:
            # notification_event_cat = sub.notificationEventCat
            # - If the notificationEventCat attribute is set, the Notify request
            #   primitive shall employ the Event Category parameter as given in the
            #   notificationEventCat attribute. Then continue with the next step

            if sub.notificationEventCat:
                pass
                # todo: what does this mean?

        # - If the notificationEventCat attribute is not configured,then
        #   continue with other step
            else:
                pass
        except AttributeError:
            pass

        try:
            latest_notify = sub.latestNotify
        # Step 2.3 Check the latestNotify attribute:
        # - If the latestNotify attribute is set, the Originator shall assign
        #   Event Category parameter of value 'latest' of the notifications
        #   generated pertaining to the subscription created. Then continue with
        #   other step
            if latest_notify:
                pass
        except AttributeError:
            pass

        # NOTE: The use of some attributes such as rateLimit, `Notify and
        # preSubscriptionNotify is not supported in this release of the(
        # document.

        try:
            batch_notify = sub.batchNotify
            
            if batch_notify == None:
                self._send_notification(resource, sub)
            else:
                current_time = datetime.datetime.now()
                notifications = self.subscriptions_info[sub.resourceID]["not"]

                for uri in sub.notificationURI:
                    notifications.append(
                        Notification(
                            notificationEvent=NotificationEventC(
                                representation=resource
                            ),
                            subscriptionReference=self._get_subscription_reference(uri, sub.path),
                            creator=sub.creator
                        )
                    )

                if int(batch_notify.number) <= len(notifications) or \
                        int(batch_notify.duration) <= int((current_time - self.subscriptions_info[sub.resourceID]["levt"]).seconds):
                    aggregated_notification = AggregatedNotification(**{"notification": notifications})

                    self._send_notification(aggregated_notification, sub)
                    self.subscriptions_info[sub.resourceID]["levt"] = current_time
                    self.subscriptions_info[sub.resourceID]["not"] = []
        except AttributeError:
            pass

        # Step 3.0 The Originator shall check the notification and reachability
        # schedules, but the notification schedules may be checked in different
        # order.
        # - If the <subscription> resource associated with the modified resource
        #   includes a <notificationSchedule> child resource, the Originator
        #   shall check the time periods given in the scheduleElement attribute
        #   of the <notificationSchedule> child resource.
        # - Also, the Originator shall check the reachability schedule
        #   associated with the Receiver by exploring its <schedule> resource.
        #   If reachability schedules are not present in a Node then that Entity
        #   is considered to be always reachable
        # - If notificationSchedule and reachability schedule indicate that
        #   message transmission is allowed, then proceed with step 5.0.
        #   Otherwise, proceed with step 4.0
        # - In particular, if the notificationEventCat attribute is set to
        #   ''immediate'' and the <notificationSchedule> resource does not allow
        #   transmission, then go to step 5.0 and send the corresponding Notify
        #   request primitive by temporarily ignoring the Originator''s
        #   notification schedule

        # Step 4.0 Check the pendingNotification attribute:
        # - If the pendingNotification attribute is set, then the Originator
        #   shall cache pending Notify request primitives according to the
        #   pendingNotification attribute. The possible values are
        #   ''sendLatest'' and ''sendAllPending''. If the value of
        #   pendingNotification is set to ''sendLatest'', the most recent Notify
        #   request primitive shall be cached by the Originator and it shall set
        #   the Event Category parameter to ''latest''. If pendingNotification
        #   is set to ''sendAllPending'', all Notify request primitives shall be
        #   cached by the Originator. If the pendingNotification attribute is
        #   not configured, the Originator shall discard the corresponding
        #   Notify request primitive. The processed Notify request primitive by
        #   the pendingNotification attribute is sent to the Receiver after the
        #   reachability recovery (see the step 6.0)

        # Step 5.0 Check the expirationCounter attribute:
        # - If the expirationCounter attribute is set, then it shall be
        #   decreased by one when the Originator successfully sends the Notify
        #   request primitive. If the counter equals to zero('0'), the
        #   corresponding <subscription> resource shall be deleted. Then end the
        #   'Compose Notify Request Primitive' procedure If the
        #   expirationCounter attribute is not configured, then end the 'Compose
        #   Notify Request Primitive' procedure

        # Originator: After reachability recovery, the Originator shall execute
        # the following steps in order:

        # Step 6.0 If the pendingNotification attribute is set, the Originator
        # shall send the processed Notify request primitive by the
        # pendingNotification attribute and, then continue with the step 7.0

        # Step 7.0 Check the expirationCounter attribute:
        # If the expirationCounter attribute is set, then its value shall be
        # decreased by one when the Originator successfully sends the Notify
        # request primitive. If the counter meets zero, the corresponding
        # <subscription> resource shall be deleted. Then end the 'Compose Notify
        # Request Primitive' procedure.
        # - If the expirationCounter attribute is not configured, then end the
        #   'Compose Notify Request Primitive' procedure

        # Receiver: When the Hosting CSE receives a Notify request primitive,
        # the Hosting CSE shall check validity of the primitive parameters. In
        # case the Receiver is a transit CSE which forwards or aggregates Notify
        # request primitives before sending to the subscriber or other transit
        # CSEs, upon receiving the Notify request primitive with the Event
        # Category parameter set to 'latest', the Receiver shall identify the
        # latest Notify request primitive with the same subscription reference
        # while storing Notify request primitives locally. When the Receiver as
        # a transit CSE needs to send pending Notify request primitives, it
        # shall send the latest Notify request primitive.

    def _get_subscription_reference(self, to, path):
        if to.startswith('//'):
            return self._abs_cse_id + '/' + path
        elif to.startswith('/'):
            return self._rel_cse_id + '/' + path
        else:
            return path

    def _send_notification(self, resource, sub):
        self.logger.debug("sending notification for resource: %s", resource)

        if isinstance(resource, AggregatedNotification):
            for uri in sub.notificationURI:
                self.api.handle_onem2m_request(OneM2MRequest(
                    op=OneM2MOperation.notify,
                    to=uri,
                    pc=resource
                ))
        else:
            for uri in sub.notificationURI:
                self.api.handle_onem2m_request(OneM2MRequest(
                    op=OneM2MOperation.notify,
                    to=uri,
                    pc=Notification(
                        notificationEvent=NotificationEventC(
                            representation=resource
                        ),
                        subscriptionReference=self._get_subscription_reference(uri, sub.path),
                        # TODO(rst): check if this is the sub creator or the creator of the notification
                        # TODO          in this case the CSE
                        creator=sub.creator
                    ),
                ))