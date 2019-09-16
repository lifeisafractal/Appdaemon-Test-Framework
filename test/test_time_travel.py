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


class Test_fast_forward:
    @staticmethod
    @pytest.fixture
    def automation_at_noon(automation, time_travel):
        time_travel.reset_time(datetime.datetime(2010, 1, 1, 12, 0))
        return automation

    class Test_to:
        def test_to_time_in_future(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.time(15, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 1, 15, 0)

        def test_to_time_in_past_goes_to_tomorrow(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.time(11, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 2, 11, 0)

        def test_to_datetime(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.datetime(2010, 1, 15, 11, 0))
            assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 15, 11, 0)

        def test_to_datetime_in_past_raises_exception(self, time_travel, automation_at_noon):
            with pytest.raises(Exception):
                time_travel.fast_forward().to(datetime.datetime(2009, 1, 15, 11, 0))

        def test_to_negative_timedelta_raises_exception(self, time_travel, automation_at_noon):
            with pytest.raises(Exception):
                time_travel.fast_forward().to(datetime.timedelta(minutes=-10))

        def test_to_datetime(self, time_travel, automation_at_noon):
            time_travel.fast_forward().to(datetime.timedelta(hours=5))
            assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 1, 17, 0)

    def test_seconds(self, time_travel, automation_at_noon):
        time_travel.fast_forward(600).seconds()
        assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 1, 12, 10)

    def test_minutes(self, time_travel, automation_at_noon):
        time_travel.fast_forward(90).minutes()
        assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 1, 13, 30)

    def test_hours(self, time_travel, automation_at_noon):
        time_travel.fast_forward(3).hours()
        assert automation_at_noon.datetime() == datetime.datetime(2010, 1, 1, 15, 00)


class Test_run_in:
    def test_callbacks_are_run_in_time_order(self, time_travel, automation):
        first_mock = mock.Mock()
        second_mock = mock.Mock()
        third_mock = mock.Mock()
        manager = mock.Mock()
        manager.attach_mock(first_mock, 'first_mock')
        manager.attach_mock(second_mock, 'second_mock')
        manager.attach_mock(third_mock, 'third_mock')

        automation.run_in(second_mock, 20)
        automation.run_in(third_mock, 30)
        automation.run_in(first_mock, 10)

        time_travel.fast_forward(30).seconds()

        expected_call_order = [mock.call.first_mock({}), mock.call.second_mock({}), mock.call.third_mock({})]
        assert manager.mock_calls == expected_call_order

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