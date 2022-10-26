def object_action(
    label=None,
    parameter_name=None,
    confirmation=None,
    permission=None,
    extra_classes=None,
    condition=None,
    display_as_disabled_if_condition_not_met=False,
    log_message=None,
    perform_after_saving=False,
    include_in_queryset_actions=True,
    after_queryset_action_callable=None,
):
    def decorator(func):
        func.label = label or func.__name__
        func.parameter_name = "_" + func.__name__ or parameter_name

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
        func.include_in_queryset_actions = include_in_queryset_actions
        if include_in_queryset_actions:
            func.func_queryset = lambda admin, request, queryset: admin.perform_object_action_on_queryset(
                func, request, queryset
            )
            if after_queryset_action_callable is not None:
                func.after_queryset_action_callable = after_queryset_action_callable
        return func

    return decorator
