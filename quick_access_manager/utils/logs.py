import os


def write_log(log_msg, enable_debug=False):

    enable_debug = True

    if enable_debug:
        # Get the directory where this file is located (utils folder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to story_editor, then into logs folder
        log_file = os.path.join(os.path.dirname(current_dir), "logs", "log.txt")

        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    else:
        pass
