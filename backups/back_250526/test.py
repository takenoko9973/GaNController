from libs.ibeam import ibeam
from utils.log_file import LogFile, LogFileManager

PROTOCOL = "HC"

log_file_manager = LogFileManager()

latest_log = log_file_manager.get_latest_log_file()
update_major = latest_log.protocol != PROTOCOL
log_file = log_file_manager.create_log_file(PROTOCOL, update_major)
try:
    laser = ibeam(f"COM{1}")
except Exception as e:
    print(f"Error: {e}")
finally:
    print("hoge")

print("END")
print("END")
print("END")
print("END")
