from appdaemon.plugins.hass.hassapi import Hass
from appdaemontestframework import automation_fixture
import mock
import pytest
import datetime

class MockAutomation(Hass):
    def initialize(self):
        pass


@automation_fixture(MockAutomation)
def automation():
    pass

#class test_time_retrieval_mocks():


class TestFastForward():
    class TestTo():
        def test_to_time_in_future(self, time_travel, automation):
            time_travel.reset_time(datetime.datetime(2010, 1, 1, 12, 0))
            time_travel.fast_forward().to(datetime.time(15, 0))
            assert automation.datetime() == datetime.datetime(2010, 1, 1, 15, 0)

        def test_to_time_in_past_goes_to_tomorrow(self, time_travel, automation):
            time_travel.reset_time(datetime.datetime(2010, 1, 1, 12, 0))
            time_travel.fast_forward().to(datetime.time(11, 0))
            assert automation.datetime() == datetime.datetime(2010, 1, 2, 11, 0)

        def test_to_datetime(self, time_travel, automation):
            time_travel.reset_time(datetime.datetime(2010, 1, 1, 12, 0))
            time_travel.fast_forward().to(datetime.datetime(2010, 1, 15, 11, 0))
            assert automation.datetime() == datetime.datetime(2010, 1, 15, 11, 0)

        def test_to_datetime_in_past_raises_exception(self, time_travel, automation):
            with pytest.raises(Exception):
                time_travel.reset_time(datetime.datetime(2010, 1, 1, 12, 0))
                time_travel.fast_forward().to(datetime.datetime(2009, 1, 15, 11, 0))

        def test_to_negative_timedelta_raises_exception(self, time_travel, automation):
            with pytest.raises(Exception):
                time_travel.fast_forward().to(datetime.timedelta(minutes=-10))


def test_callback_not_called_before_timeout(time_travel, automation):
    foo = mock.Mock()
    automation.run_in(foo, 10)
    time_travel.fast_forward(5).seconds()
    foo.assert_not_called()


def test_callback_called_after_timeout(time_travel, automation):
    scheduled_callback = mock.Mock(name="Scheduled Callback")
    automation.run_in(scheduled_callback, 10)
    time_travel.fast_forward(20).seconds()
    scheduled_callback.assert_called()


def test_canceled_timer_does_not_run_callback(time_travel, automation):
    foo = mock.Mock()
    handle = automation.run_in(foo, 10)
    time_travel.fast_forward(5).seconds()
    automation.cancel_timer(handle)
    time_travel.fast_forward(10).seconds()
    foo.assert_not_called()

# Make sure they are called in time order