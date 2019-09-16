import uuid
import datetime

class TimeTravelWrapper:
    """
    AppDaemon Test Framework Utility to simulate going forward in time
    """

    def __init__(self, hass_functions):
        self.scheduler_mocks = SchedulerMocks()

        # hass_functions['time'].side_effect = self.scheduler_mocks.time_mock
        # hass_functions['date'].side_effect = self.scheduler_mocks.date_mock
        # hass_functions['datetime'].side_effect = self.scheduler_mocks.datetime_mock
        mock_funcs = {
            'run_in': self.scheduler_mocks.run_in_mock,
            #s'run_every': self.scheduler_mocks.run_every_mock,
            'cancel_timer': self.scheduler_mocks.cancel_timer_mock,
            'get_now': self.scheduler_mocks.get_now_mock,
            'get_now_ts': self.scheduler_mocks.get_now_ts_mock,
            'AD.sched.insert_schedule': self.scheduler_mocks.insert_schedule_mock,
        }
        for hass_function, mock in mock_funcs.items():
            hass_functions[hass_function].side_effect = mock

    def reset_time(self, time):
        """Rest the time of the simulation. You can not call this once you have registed any callbacks

        if time is a datetime, it will set to that absolution time.
        if time is just a time, it will set the time, but leave the day the same.

        Format:
        > time_travel.reset_time(datetime.datetime(2019, 04, 05, 14, 13))
        > # or if you don't care about the date
        > time_travel.reset_time(datetime.time(14, 13))
        """
        self.scheduler_mocks.reset_time(time)

    def fast_forward(self, duration=None):
        """
        Simulate going forward in time.

        It calls all the functions that have been registered with AppDaemon
        for a later schedule run. A function is only called if it's scheduled
        time is before or at the simulated time.

        You can chain the calls and call `fast_forward` multiple times in a single test

        Format:
        > time_travel.fast_forward(10).minutes()
        > # Or
        > time_travel.fast_forward(30).seconds()
        > # or
        > time_travel.fast_forward(3).hours()
        > # or
        > time_travel.fast_forward().to(datetime.time(14, 55))
        """
        if duration:
            return UnitsWrapper(duration, self._fast_forward_seconds)
        else:
            return AbsoluteWrapper(self.scheduler_mocks.fast_forward)

    def assert_current_time(self, expected_current_time):
        """
        Assert the current time is as expected

        Expected current time is expressed as a duration from T = 0

        Format:
        > time_travel.assert_current_time(10).minutes()
        > # Or
        > time_travel.assert_current_time(30).seconds()
        """
        return UnitsWrapper(expected_current_time, self._assert_current_time_seconds)

    def _fast_forward_seconds(self, seconds_to_fast_forward):
        self.scheduler_mocks.fast_forward(datetime.timedelta(seconds=seconds_to_fast_forward))

    def _assert_current_time_seconds(self, expected_seconds_from_start):
        assert self.scheduler_mocks.elapsed_seconds() == expected_seconds_from_start


class AbsoluteWrapper:
    def __init__(self, function_for_to_set_absolute_time):
        self.function_for_to_set_absolute_time = function_for_to_set_absolute_time

    def to(self, time):
        self.function_for_to_set_absolute_time(time)


class UnitsWrapper:
    def __init__(self, duration, function_with_arg_in_seconds):
        self.duration = duration
        self.function_with_arg_in_seconds = function_with_arg_in_seconds

    def hours(self):
        self.function_with_arg_in_seconds(self.duration * 60 * 60)

    def minutes(self):
        self.function_with_arg_in_seconds(self.duration * 60)

    def seconds(self):
        self.function_with_arg_in_seconds(self.duration)


class CallbackInfo:
    """Class to hold info about a scheduled callback"""
    def __init__(self, callback_function, kwargs, run_date_time):
        self.handle = str(uuid.uuid4())
        self.run_date_time = run_date_time
        self.callback_function = callback_function
        self.kwargs = kwargs

    def __call__(self):
        self.callback_function(self.kwargs)


class SchedulerMocks:
    """Class to provide functional mocks for the AppDaemon HASS scheduling functions"""
    def __init__(self):
        self.all_registered_callbacks = []
        # Default to Jan 1st, 2015 12:00AM
        self.reset_time(datetime.datetime(2015, 1, 1, 0, 0))

    ### Hass mock functions
    def get_now_mock(self):
        return self.now

    def get_now_ts_mock(self):
        return self.now.timestamp()

    def insert_schedule_mock(self, name, aware_dt, callback, repeat, type_, **kwargs):
        self._queue_calllback(callback, kwargs, aware_dt)

    def run_in_mock(self, callback, delay_in_s, **kwargs):
        run_date_time = self.now + datetime.timedelta(seconds=delay_in_s)
        return self._queue_calllback(callback, kwargs, run_date_time)

    def run_daily_mock(self, callback, delay_in_s, **kwargs):
        pass

    def run_every_mock(self, callback, start, interval, **kwargs):
        assert False
        pass

    def cancel_timer_mock(self, handle):
        for callback in self.all_registered_callbacks:
            if callback.handle == handle:
                self.all_registered_callbacks.remove(callback)

    ### Test framework functions
    def reset_time(self, time):
        if len(self.all_registered_callbacks) != 0:
            raise RuntimeError("You can not reset time with pending callbacks")

        if type(time) == datetime.time:
            time = datetime.datetime.combine(self.now.date(), time)
        self.now = time
        self.start_time = self.now

    def elapsed_seconds(self):
        return (self.now - self.start_time).total_seconds()

    def cancel_all_callbacks(self):
        """Clears all currently registed callbacks"""
        self.all_registered_callbacks = []

    def fast_forward(self, time):
        """Fastforward time and invoke callbacks. time can be a timedelta, time, or datetime"""
        if type(time) == datetime.timedelta:
            target_datetime = self.now + time
        elif type(time) == datetime.time:
            if time > self.now.time():
                target_datetime = datetime.datetime.combine(self.now.date(), time)
            else:
                # handle wrap around to next day if time is in the past already
                target_date = self.now.date() + datetime.timedelta(days=1)
                target_datetime = datetime.datetime.combine(target_date, time)
        elif type(time) == datetime.datetime:
            target_datetime = time
        self._run_callbacks_and_advance_time(target_datetime)

    ### Internal functions
    def _queue_calllback(self, callback_function, kwargs, run_date_time):
        """queue a new callback and return its handle"""
        new_callback = CallbackInfo(callback_function, kwargs, run_date_time)
        if new_callback.run_date_time < self.now:
            raise ValueError("Can not schedule events in the past")
        self.all_registered_callbacks.append(new_callback)
        return new_callback.handle

    def _run_callbacks_and_advance_time(self, target_datetime):
        """run all callbacks scheduled between now and target_datetime"""
        if target_datetime <= self.now:
            raise ValueError("You can not fast forward to a time in the past.")
        callbacks_to_run = [x for x in self.all_registered_callbacks if x.run_date_time <= target_datetime]
        # sort so we call them in the order from oldest to newest
        callbacks_to_run.sort(key=lambda cb: cb.run_date_time)

        for callback in callbacks_to_run:
            self.now = callback.run_date_time
            callback()
            self.all_registered_callbacks.remove(callback)

        self.now = target_datetime


class Test_run_in:
    pass


class Test_run_at:
    pass
