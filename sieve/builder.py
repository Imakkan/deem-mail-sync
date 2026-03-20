from sieve.enumerate import Actions, Conditions, Requires
from sieve.utils import construct_sieve_mime_body


class ConditionBuilder:

    @classmethod
    def build_conditions(cls, user_email: str, conditions: list, rule_conditions: list):
        for condition in rule_conditions:
            if condition['name'] == str(Conditions.RECEIVED_FROM):
                ConditionBuilder.received_from_condition(conditions, condition['arguments'])
            if condition['name'] == str(Conditions.MY_NAME_TO):
                ConditionBuilder.my_name_to(conditions, condition['arguments'])
            if condition['name'] == str(Conditions.MY_NAME_CC):
                ConditionBuilder.my_name_cc(conditions, user_email)
        return conditions

    @classmethod
    def received_from_condition(cls, conditions: list, arguments: list):
        for user in arguments:
            conditions.append(("from", ":contains", user))
        return conditions

    @classmethod
    def my_name_to(cls, conditions: list, arguments: list):
        for user in arguments:
            conditions.append(("to", ":contains", user))
        return conditions

    @classmethod
    def my_name_cc(cls, conditions: list, user_email: str):
        conditions.append(("cc", ":contains", user_email))
        return conditions


class ActionBuilder:

    @classmethod
    def build_actions(cls, requires: list, actions: list, rule_actions: list):
        for action in rule_actions:
            if action['name'] == str(Actions.MOVE_TO):
                cls.move_to_folder(requires, actions, action['arguments'][0])
            if action['name'] == str(Actions.DELETE):
                cls.delete_email(actions)
            if action['name'] == str(Actions.REPLY):
                cls.auto_reply(requires, actions, action['arguments'][0], action['arguments'][1],
                               action['arguments'][2])
        return actions

    @classmethod
    def move_to_folder(cls, requires: list, actions: list, folder_name: str):
        if Requires.FILE_INTO not in requires:
            requires.append(Requires.FILE_INTO)
        actions.append((Requires.FILE_INTO, folder_name))
        return actions

    @classmethod
    def delete_email(cls, actions: list):
        actions.append(("discard", ""))
        return actions

    @classmethod
    def auto_reply(cls, requires: list, actions: list, subject: str, body: str, styled_body: str):
        if Requires.VACATION not in requires:
            requires.append(Requires.VACATION)
        message = construct_sieve_mime_body(body, styled_body)
        actions.append((Requires.VACATION, ':subject', '"%s"' % subject, ':mime', message))
        return actions
