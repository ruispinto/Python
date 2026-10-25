
import win32evtlog
import win32con
import win32evtlogutil

def read_events(log_name="System", limits=100):
    handle = win32evtlog.OpenEventLog(None, log_name)

    flags = (
        win32evtlog.EVENTLOG_BACKWARDS_READ
        | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    )

    try:
        all_events = win32evtlog.ReadEventLog(
            handle, flags, 0
        )

        all = ""
        ev = {}

        counter = 0
        for e in all_events[:limits]:
            counter += 1
            all += "-" * 60
            all += "\nLog:" + log_name
            all += "\nID:" + str(e.EventID & 0xFFFF)
            all += "\nOrigin:" + e.SourceName
            all += "\nDate:" + str(e.TimeGenerated)
            all += "\nType:" + str(e.EventType)
            all += "\nSID User:" + str(e.Sid)
            event_id = str(e.EventID & 0xFFFF)
            if event_id in ev:
                ev[event_id] += 1
            else:
                ev[event_id] = 1

            try:
                message = win32evtlogutil.SafeFormatMessage(
                    e, log_name
                )
                all += "\nMessage: " + message
            except Exception:
                all += "\nMessage: unable to format"

    finally:
        win32evtlog.CloseEventLog(handle)

    print(all)
    print(f"\nTotal events read: {counter} \n")
    print(f"Event counters:")
    for event_id, count in ev.items():
        print(f"{event_id.rjust(5)}: {count} times")
    print("\n")

if __name__ == "__main__":
    read_events("System", 100)
    read_events("Application", 100)
    #read_events("Security", 100)
    input("Press Enter to exit...")
    # Also you can test "Application"
    # or "Security" (may require additional permissions).

