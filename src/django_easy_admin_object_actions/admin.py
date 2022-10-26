from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext


class ObjectActionsMixin:
    change_form_template = "easy_admin_object_actions/admin/change_form.html"

    object_actions_before_fieldsets = []
    object_actions_after_fieldsets = []
    object_actions_after_related_objects = []

    def _get_all_object_actions(self):
        """Get all object actions."""
        return (
            tuple(self.object_actions_before_fieldsets)
            + tuple(self.object_actions_after_fieldsets)
            + tuple(self.object_actions_after_related_objects)
        )

    def _get_object_actions(self, actions, request, obj=None):
        """Get object actions."""
        for action_name in actions:
            if callable(action_name):
                action = action_name
            else:
                if not hasattr(self, action_name) or not callable(
                    getattr(self, action_name)
                ):
                    continue
                action = getattr(self, action_name)

            if obj is None and not getattr(action, "perform_after_saving", True):
                continue  # no object actions before saving for new objects, as the objects don't yet exist

            has_permission = bool(
                not getattr(action, "permission", None)
                or request.user.has_perm(getattr(action, "permission"))
            )

            condition_met = bool(
                not getattr(action, "condition", None)
                or callable(getattr(action, "condition"))
                and obj
                and getattr(action, "condition")(request, obj)
            )

            if has_permission and (
                condition_met or action.disable_if_condition_not_met
            ):
                yield {
                    "func": action,
                    "label": action.label,
                    "parameter_name": action.parameter_name,
                    "confirmation": getattr(action, "confirmation", None),
                    "extra_classes": getattr(action, "extra_classes", None),
                    "disabled": not condition_met,
                    "log_message": getattr(action, "log_message", None),
                    "perform_after_saving": getattr(
                        action, "perform_after_saving", False
                    ),
                }

    def get_object_actions(self, request, obj=None):
        """Get all object actions."""
        return self._get_object_actions(self._get_all_object_actions(), request, obj)

    def _get_object_actions_after_saving(self, request, obj):
        """Get object actions that should be performed after saving."""
        return filter(
            lambda x: x["perform_after_saving"], self.get_object_actions(request, obj)
        )

    def _get_object_actions_before_saving(self, request, obj):
        """Get object actions that should be performed before saving."""
        if obj is None:
            return (
                []
            )  # no object actions before saving for new objects, as the objects don't yet exist
        return filter(
            lambda x: not x["perform_after_saving"],
            self.get_object_actions(request, obj),
        )

    def perform_object_action(self, action, request, obj):
        """Perform the object action."""
        if action["log_message"]:
            self.log_change(request, obj, action["log_message"])
        return action["func"](request, obj)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Perform object action before saving."""
        obj = self.get_object(request, object_id)
        for action in self._get_object_actions_before_saving(request, obj):
            if request.POST.get(action["parameter_name"]) and not action["disabled"]:
                response = self.perform_object_action(action, request, obj)
                if response and issubclass(response.__class__, HttpResponse):
                    return response

        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        """Perform object action after saving."""
        for action in self._get_object_actions_after_saving(request, obj):
            if request.POST.get(action["parameter_name"]) and not action["disabled"]:
                response = self.perform_object_action(action, request, obj)
                if response and issubclass(response.__class__, HttpResponse):
                    return response  # return to the return value of the action
                else:
                    return redirect(request.path)  # return to the same page

        return super().response_change(request, obj)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """Add object actions to the context."""
        context["object_actions_before_fieldsets"] = self._get_object_actions(
            self.object_actions_before_fieldsets, request, obj
        )
        context["object_actions_after_fieldsets"] = self._get_object_actions(
            self.object_actions_after_fieldsets, request, obj
        )
        context["object_actions_after_related_objects"] = self._get_object_actions(
            self.object_actions_after_related_objects, request, obj
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def _get_queryset_object_actions(self, actions, request):
        """Get queryset object actions."""
        for action_name in actions:
            if callable(action_name):
                action = action_name
            else:
                if not hasattr(self, action_name) or not callable(
                    getattr(self, action_name)
                ):
                    continue
                action = getattr(self, action_name)

            if not action.include_in_queryset_actions:
                continue

            has_permission = bool(
                not getattr(action, "permission", None)
                or request.user.has_perm(getattr(action, "permission"))
            )

            if has_permission:
                yield {
                    "func": action.func_queryset,
                    "short_description": action.label,
                    "name": action.parameter_name,
                }

    def get_queryset_object_actions(self, request):
        """Get all queryset object actions."""
        return self._get_queryset_object_actions(
            self._get_all_object_actions(), request
        )

    def get_actions(self, request):
        """Add queryset object actions to the actions."""
        actions = super().get_actions(request)
        object_actions = {
            action["name"]: (
                action["func"],
                action["name"],
                action["short_description"],
            )
            for action in self.get_queryset_object_actions(request)
        }
        return actions | object_actions

    def perform_object_action_on_queryset(self, action, request, queryset):
        """Perform the object action on the queryset."""
        if hasattr(action, "permission") and not request.user.has_perm(
            action.permission
        ):
            return

        count = 0

        for obj in queryset:
            if (
                hasattr(action, "condition")
                and callable(action.condition)
                and not action.condition(request, obj)
            ):
                continue

            if hasattr(action, "log_message"):
                self.log_change(request, obj, action.log_message)

            return_value = action(self, request, obj)

            if bool(return_value):
                count += 1

        if hasattr(action, "after_queryset_action_callable") and callable(
            action.after_queryset_action_callable
        ):
            action.after_queryset_action_callable(request, queryset, count)
        else:
            msg = gettext("Applied '%(action_message)s' on %(count)s %(name)s.") % {
                "action_message": action.label,
                "count": count,
                "name": model_ngettext(self.opts, count),
            }
            self.message_user(request, msg, messages.SUCCESS)
