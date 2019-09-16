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
        @staticmethod
        @pytest.fixture
        def automation_at_noon(automation, time_travel):
            time_travel.reset_time(datetime.time(12,0))
            return automation

        def test_to_time_in_future(self, time_travel, automation_at_noon):
            start = automation_at_noon.datetime()
            time_travel.fast_forward().to(datetime.time(15, 0))
            elapsed_time = automation_at_noon.datetime() - start
            assert elapsed_time == datetime.timedelta(hours=3)

        def test_to_time_in_past_goes_to_tomorrow(self, time_travel, automation_at_noon):
            start = automation_at_noon.datetime()
            time_travel.fast_forward().to(datetime.time(11, 0))
            elapsed_time = automation_at_noon.datetime() - start
            assert elapsed_time == datetime.timedelta(hours=23)

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