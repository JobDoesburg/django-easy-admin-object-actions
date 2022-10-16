# Django easy admin object actions

Django easy admin object actions is a Django app that allows you easily to add buttons to an object's admin change form page, to perform certain actions on the object.

In this documentation, we use the term "object" to refer to the model instance that is being edited in the admin change form.
As an example, we will consider an invoice model that has a status field, and we try to add a button to the change form page that allows us to send the invoice. There are, of course, many other use cases for this app.

## Installation
1. Install using pip:
    ```bash
    pip install django-easy-admin-object-actions
    ```
2. Add `django_easy_admin_object_actions` to your `INSTALLED_APPS`:
    ```python
    INSTALLED_APPS = [
        ...
        'django_easy_admin_object_actions',
        ...
    ]
    ```
3. Use the `ObjectActionsMixin` in your admin classes:
    ```python
    from django.contrib import admin
    from django_easy_admin_object_actions.admin import ObjectActionsMixin

    class MyModelAdmin(ObjectActionsMixin, admin.ModelAdmin):
        ...
    ```
4. Implement object actions in your admin classes:
    ```python
    from django_easy_admin_object_actions.decorators import object_action

    class MyModelAdmin(ObjectActionsMixin, admin.ModelAdmin):
        ...

        @object_action(
            label="Send invoice",
            parameter_name="_sendinvoice",
        )
        def send_invoice(self, request, obj):
            obj.send_invoice()
    ```
5. Add the object action to the `object_actions_before_fieldsets`, `object_actions_after_fieldsets`, or `object_actions_after_related_objects` attributes of your admin, depending on where you want the action to appear:
    ```python
    class MyModelAdmin(ObjectActionsMixin, admin.ModelAdmin):
        object_actions_before_fieldsets = ["send_invoice"] # Displayed at the top of the page before the change form's fieldsets
        object_actions_after_fieldsets = ["send_invoice"] # Displayed at the bottom of the page after the change form's fieldsets, but before any inlines (related objects)
        object_actions_after_related_objects = ["send_invoice"] # Displayed at the bottom of the page after the change form's fieldsets and inlines (related objects), right above the submit row
    ```
## Usage

There are numerous ways to use this package. Here are some examples:
- Some models try to emulate some kind of state machine. For example, an invoice model might have a `state` field with values `draft`, `sent`, and `paid`. You can use object actions to implement the transitions between these states. For example, you can add an object action to send an invoice, which will change the status from `draft` to `sent` and send out an email. You can also add an object action to mark an invoice as paid, which will change the status from `sent` to `paid`. Here, the `conditon` argument could be extra useful.
- You can use object actions to implement a more explicit user interface to perform actions, similar to the functionality Django's default admin `actions` already provides for querysets. Normally these actions are only available in the `changelist` view via a dropdown box. With object actions, you can add them to the `changeform` view as well.
- The `confirmation` argument can be used to add an extra confirmation step to an object action. This can be useful if the action is destructive or irreversible.
- Object actions can be used to easily redirect users to different pages. For example, you could add an object action to redirect users viewing the details of an invoice to a page where they can pay the invoice or view the customer's details in an external CRM: `return HttpResponseRedirect('https://crm.example.com/customer/{}'.format(obj.customer.id))`

### Available arguments for `object_action`
- `label`: The label of the action button.
- `parameter_name`: The name of the parameter that is used in the POST body to perform the action.
- `confirmation`: A confirmation message that is alerted to the user when the action is performed. If `None`, no confirmation is required.
- `permission`: A permission string that the user should have in order to perform the action. This check is done via `request.user.has_perm(permission)`. Note that this does *not* use the admin `has_<perm>_permission(request, obj)` methods that might have been overwritten for your admin.
- `extra_classes`: A list of extra classes that are added to the action button. For example, `default` will make the button appear as a primary button.
- `condition`: A function that determines whether the action should be shown. It should take the object and the request as an argument and should return a boolean. If the function returns `False`, the action cannot be used. For example, you can use this to only show the action if the object is in a certain state: `condition=lambda obj, request: obj.state == "draft"`.
- `display_as_disabled_if_condition_not_met`: If `True`, the action button will be displayed as disabled if the condition is not met. If `False`, the action button will not be displayed at all if the condition is not met. Defaults to `True`.
- `log_message`: A message that is logged when the action is performed. If `None`, no message is logged. For example, you can use this to log the action to the object's history: `log_message="Invoice sent"`. 
- `perform_after_saving`: If `True`, the action is performed after any changes made in the object's form are saved. If `False`, the action is performed before the object is saved. Defaults to `False`.

### Return values for object actions
The actual action should return either `None` (or not return anything), or a `HttpResponse` object. If the action returns a `HttpResponse` object, the response is returned to the user instead of the default behavior of redirecting to the object's change page.
This has the following implications:

- If `perform_after_saving` is set to `False` and your action returns a `HttpResponse` object, only the action will be executed, but any changes made in the form will *not* be processed.
- If `perform_after_saving` is set to `False` and your action returns `None`, the action will be executed and afterwards, the form data will be processed. This means that the action will be executed even if the form data is invalid. This can result in unexpected behaviour if the action changes the object in a way that is not compatible with the form data.
- If `perform_after_saving` is set to `True`, first any changes made in the form will be processed and then the action will be executed. Depending on the action's return value, the user will either be redirected to the object's change page or the response returned by the action will be returned to the user. Note that the `condition` will be re-evaluated after the form data is processed, so the action might not actually be performed if the condition is not met anymore!

