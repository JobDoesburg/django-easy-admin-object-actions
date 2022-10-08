class ObjectActionsMixin:
    change_form_template = "easy_admin_object_actions/admin/change_form.html"

    object_actions_before_fieldsets = []
    object_actions_after_fieldsets = []
    object_actions_after_related_objects = []

    def _get_all_object_actions(self):
        return (
            tuple(self.object_actions_before_fieldsets)
            + tuple(self.object_actions_after_fieldsets)
            + tuple(self.object_actions_after_related_objects)
        )

    def _get_object_actions(self, actions, request, obj=None):
        for action_name in actions:
            if callable(action_name):
                action = action_name
            else:
                if not hasattr(self, action_name) or not callable(
                    getattr(self, action_name)
                ):
                    continue
                action = getattr(self, action_name)

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
        return self._get_object_actions(self._get_all_object_actions(), request, obj)

    def _get_object_actions_after_saving(self, request, obj):
        return filter(
            lambda x: x["perform_after_saving"], self.get_object_actions(request, obj)
        )

    def _get_object_actions_before_saving(self, request, obj):
        return filter(
            lambda x: not x["perform_after_saving"],
            self.get_object_actions(request, obj),
        )

    def perform_object_action(self, action, request, obj):
        if action["log_message"]:
            self.log_change(request, obj, action["log_message"])
        return action["func"](request, obj)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        for action in self._get_object_actions_before_saving(request, obj):
            if request.POST.get(action["parameter_name"]) and not action["disabled"]:
                response = self.perform_object_action(action, request, obj)
                if response:
                    return response

        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        for action in self._get_object_actions_after_saving(request, obj):
            if request.POST.get(action["parameter_name"]) and not action["disabled"]:
                response = self.perform_object_action(action, request, obj)
                if response:
                    return response

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
