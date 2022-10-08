def object_action(
    label,
    parameter_name,
    permissions=None,
    description=None,
    extra_classes=None,
    condition=None,
    display_as_disabled_if_condition_not_met=False,
    display_position="after_related_objects",
    log_message=None,
    perform_after_saving=False,
):
    def decorator(func):
        func.label = label
        func.parameter_name = parameter_name
        if permissions is not None:
            func.allowed_permissions = permissions
        if description is not None:
            func.short_description = description
        func.extra_classes = extra_classes
        if condition is not None:
            func.condition = condition
        func.display_position = display_position
        func.disable_if_condition_not_met = display_as_disabled_if_condition_not_met
        func.log_message = log_message
        func.perform_after_saving = perform_after_saving
        return func

    return decorator
