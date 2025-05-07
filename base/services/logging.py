import traceback
import datetime


class LoggingService:
    def get_first_error(self, errors):

        if isinstance(errors, dict):
            first_field_errors = next(iter(errors.values()))
            if isinstance(first_field_errors, list):
                return first_field_errors[0]
            return self.get_first_error(first_field_errors)

        elif isinstance(errors, list):
            return errors[0]

        return str(errors)

    def check_required_fields(self, data, required_fields):
        """
        This gets the data, checks the required fields. it returns something like this:
        "field: name, email are required"
        """
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            if len(missing_fields) == 1:
                return f"Field: {missing_fields[0]} is required"
            else:
                formatted_fields = ", ".join(missing_fields)
                return f"Fields: {formatted_fields} are required"

        return None

    def log_error(self, error, error_type="message"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(error, Exception):
            print(f"[{timestamp}] {error_type.upper()} ERROR:")
            print(f"Error message: {str(error)}")
            print("Traceback:")
            print(traceback.format_exc())
        else:
            print(f"[{timestamp}] {error_type.upper()}: {error}")
