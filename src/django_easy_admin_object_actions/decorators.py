def object_action(
    label,
    parameter_name,
    confirmation=None,
    permission=None,
    extra_classes=None,
    condition=None,
    display_as_disabled_if_condition_not_met=False,
    log_message=None,
    perform_after_saving=False,
):
    def decorator(func):
        func.label = label
        func.parameter_name = parameter_name
        if confirmation is not None:
            func.confirmation = confirmation
        if permission is not None:
            func.permission = permission
        func.extra_classes = extra_classes
        if condition is not None:
            func.condition = condition
        func.disable_if_condition_not_met = display_as_disabled_if_condition_not_met
        if log_message is not None:
            func.log_message = log_message
        func.perform_after_saving = perform_after_saving
        return func

    return decorator
