class AdminAjaxMixin:

    @staticmethod
    def get_ajax_value(source, key, default=None):
        value = source.get(key, default)
        if value and isinstance(value, list):
            return value[0]
        return value

    def get_ajax_bool(self, source, key):
        positives = 'true', 'on', 'yes', 'y', '1'
        value = self.get_ajax_value(source, key, False)
        return str(value).lower() in positives

    def check_multiple_bools(self, urlparams, *fields, check_type: str = 'or'):
        if not isinstance(check_type, str) or not check_type.lower() in ('and', 'or'):
            raise AttributeError('Check type must be \'and\' or \'or\'!')
        check_items = [self.get_ajax_bool(urlparams, field) for field in fields]
        if check_type.lower() == 'or':
            return any(check_items)
        return all(check_items)
