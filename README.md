# Description

OccuSim is a versatile Occupation Simulator for the [AppDaemon](https://github.com/acockburn/appdaemon) Platform.

# Installation

## Clone the Repository

``` bash
$ git clone https://github.com/acockburn/occusim.git
```

Next copy the occusim.py app to your Apps directory (see [AppDaemon docs](https://github.com/acockburn/appdaemon/blob/master/API.md) for more information)

# Configuration

OccuSim is configured in the standard way with a named stanza in the appdaemon.yaml file for the app - or more than one if you prefer. There are a number of initial parameters that control the behavior, then parameters to define the various activities and times. The initial parameters are as follows:

```
Occupancy Simulator:
  class: OccuSim
  module: occusim
  log_msg: '1'
  notify: '1'
  enable: input_boolean.vacation,on
  test: '1'
  dump_times: '1'
  reset_time: 02:00:00
```

- `log_msg` set this to any value to make `OccuSim` log its scheduled activities
- `notify` set this to any value to make `OccuSim` send a notification for its scheduled activities to the default notify.notify service in Home Assistant
- `notify_service` sets the override for the notify service to be used, for instance `telegram` or `smtp` 
- `enable` (optional) set to the name of an input boolean, and the value it needs to be to enable `OccuSim`. If omitted, `OccuSim` will always be active.
- `1select` (optional) set the name of an input select that will have its value checked at execution time. If the current state of the input select matches any of the listed states, occusim will be active. e.g.: `select: input_select.mode,Day,Night`
- `test` (optional) set to "1" to have occusim run, but not activate any lights or scenes. Use with `log_msg` to test settings and times. If set to anything else, or not present, test mode will not be enabled.
- `dump_times` (optional) set to any value to dump a list of the times events will happen when the app is first initialized and every night at the reset time.
- `reset_time` (optional) time at which `OccuSim` re-calculates the new set of random times for the day ahead. Defaults to 3am.

# Operation

`OccuSim` has 2 modes of operation, sequenced and random. They can be used interchangeably and one model might suit you better than the other.

## Sequenced Operation

This model is intended for households that have a predictable schedule within certain limits and where the desire is to keep the appearance of that schedule when noone is home. It consists of a number of steps which can be absolute times, random times within defined limits, times relative to sunrise and sunset, or times relative to other steps.

Each step consists of a number of parameters, and can have an unlimited number of actions to turn devices or scenes on or off.

The parameters for a given step all start with `step_<step name>_` and are grouped together by that common step name. The step name can be anything, it just needs to be the same for all parameters in the step. The parameters are as follows:

- `step_<step_name>_name` - A printable name for the Step e.g. `Morning` or `Bedtime`
- `step_<step_name>_start` - start time for this step. If no end time is specified, this will be an absolute time and takes the form `hh:mm:ss`. Alternatively, this can be an offset from sunrise or sunset, for example `sunset - 00:45:00` 
- `step_<step_name>_days` (optional) comma separated list of days (no spaces) on which the step will be active. If omitted, the step will be active every day.
- `step_<step_name>_end` (optional) - end time for random selection. If this is specified for a step, the time a step fires will be randomized between the start and end times. It takes the same parameter format as `start`
- `step_<step_name>_on_<name>` (optional) - An entity to turn on when the step fires. This can be anything that home assistant can turn on with its `homeassistant/turn_on` service - a light, a script or a scene. It is possible to have multiples of this parameter, however <name> must be unique for each one - it is easiest just to use numbers.
- `step_<step_name>_off_<name>` (optional) - An entity to turn off when the step fires. This can be anything that home assistant can turn off with its `homeassistant/turn_off` service - a light, a script or a scene. If a scene is used here, `OccuSim` is smart enough to turn it on rather than off. It is possible to have multiples of this parameter, however <name> must be unique for each one - it is easiest just to use numbers. 

If you require a step to be relative to another step, instead of using the `start` and `end` parameters, use the following 3 parameters:

- `step_<step_name>_relative` - Name of a defined step that is the start of the range of randomness (the step itself can be random, see above)
- `step_<step_name>_start_offset` - Duration after the step that is the start of the random range for this step, e.g. `00:01:00` - 1 minute.
- `step_<step_name>_end_offset` (optional) - Duration after the step that is the end of the random range for this step, e.g. `01:00:00` - 1 hour. If omitted, the step will fire at the exact offset specified in the start_offset.

## Random Operation

By Contrast, Random Operation attempts to turn various lights on and off at random times, and do that a set number of times. This pattern may work better for less structured households.

To set up a random event, it is first necessary to define 2 steps to act as the start and end times for the random activity. The steps themselves need not do turn anything on or off, they are there as markers. As with the steps described above, the parameters have a pattern of `random_<random_name>` to group the parameters together.

To define a random event, use the following parameters:

- `random_<random_name>_name` - A printable name for the Step e.g. `Morning` or `Bedtime`
- `random_<random_name>_start` - Name of a defined step that is the start of the range of randomness for this event(the step itself can be random, see above)
- `random_<random_name>_end` - Name of a defined step that is the end of the range of randomness for this event.
- `random_<random_name>_minduration` - Minimum duration of the event
- `random_<random_name>_maxduration` - Maximum duration of the event
- `random_<random_name>_number` - Number of times within the period to fire the event
- `random_<random_name>_on_<name>` - An entity to turn on at the start of the event period. This can be anything that home assistant can turn on with its `homeassistant/turn_on` service - a light, a script or a scene. It is possible to have multiples of this parameter, however <name> must be unique for each one - it is easiest just to use numbers.
- `random_<random_name>_off_<name>` - An entity to turn off at the end of the event period. This can be anything that home assistant can turn off with its `homeassistant/turn_off` service - a light, a script or a scene. If a scene is used here, `OccuSim` is smart enough to turn it on rather than off. It is possible to have multiples of this parameter, however <name> must be unique for each one - it is easiest just to use numbers.

Random events are not guaranteed to not overlap, however this can add additional randomness to the operation so is not a bad thing.

## input_selects and events

Each step can also fire a home assistant event or modify the value of an input_select to match the name of the step. Both use the on and off step parameters with special values. For instance, to send a `MODE_CHANGE` custom event, with a parameter called `mode` set to the value of the step, use the following:

```yaml
step_<step name>_on_1: event.MODE_CHANGE,mode
```

To set an input_select called `house_mode` to the value of the current step use the following:

```yaml
step_<step_name>_on_1: input_select.house_mode
```

# Example

The above parameters are somewhat complex in isolation, so let's build up a worked example to see how they work together.

## Morning

Every morning my wife gets up before me and when she gets downstairs a motion detector normally turns a light on for her - she normally gets downstairs sometime between 5:30am and 6am. To simulate that we would use:

```yaml
step_morning_name: Morning
step_morning_start: 05:30:00
step_morning_end: 06:00:00
step_morning_on_1: scene.wendys_lamp
```

## Day

When the sun rises, I have a luminance sensor turn the lights off when it gets to a certain level. I could leave that enabled but if I wanted to simulate it I could use sunrise as a way to do so - 45 minutes after sunrise is usually about right:

```yaml
step_day_name: Day
step_day_start: sunrise + 00:45:00
step_day_on_1: scene.downstairs_off
```

In this case I opted to use an exact time (at least relative to sunset) however, I could have added in an end parameter to make it a bit more random, perhaps like this:


```yaml
step_day_end: sunrise + 01:00:00
```

With that in place the lights would go off at a random time between 45 minutes and an hour after sunrise.

## Evening

In the evening, when the light gets below a certain level I turn on the downstairs lights. I can simulate this again using sunset:

```yaml
step_evening_name: Evening
step_evening_start: sunset - 00:45:00
step_evening_on_1: scene.downstairs_on
```

## Bedtime

Generally we stay with this set of lights until we go to bed when several things happen. We manually run an automation that does the following things:

- Turns the upstairs hall light on
- Turns on our bedside lights
- Waits 5 seconds and turns off the downstairs lights

We can do that with a couple of steps. First, let's turn on the hall light and our bedside lights. We will do this at a random time to simulate our varying times of going to bed.

```yaml
step_bedtime_name: Bedtime
step_bedtime_start: 21:30:00 
step_bedtime_end: 22:30:00
step_bedtime_on_1: scene.upstairs_hall_on
step_bedtime_on_2: scene.bedroom_on
```

Now, let's wait 5 seconds and turn downstairs off. I want this to be exactly 5 seconds to emulate the behavior of my existing automations. We do this using a relative step, since bedtime is random and we don't know when exactly it happened. With a relative step, the step will be fired after the step it is relative to, whenever that actually happens.

```yaml
step_downstairs_off_name: Downstairs Off
step_downstairs_off_relative: Bedtime
step_downstairs_off_start_offset: 00:00:05
step_downstairs_off_off_1: scene.downstairs_off
```

Normally we will spend a few minutes getting ready for bed, then turn the upstairs hall light off. Lets randomise that a little, but keep it relative to bedtime:

```yaml
step_upstairs_hall_off_name: Upstairs Hall Off
step_upstairs_hall_off_relative: Bedtime
step_upstairs_hall_off_start_offset: 00:01:00
step_upstairs_hall_off_end_offset: 00:05:00
step_upstairs_hall_off_off_1: scene.upstairs_hall_off
```

Then we may read for a while before turning the bedroom lights out for the night:

```yaml
step_night_name: Night
step_night_relative: Bedtime
step_night_start_offset: 00:05:00
step_night_end_offset: 01:00:00
step_night_off_1: scene.bedroom_off
```

## Evening Office

So far, the above has been fairly structured, but it would be nice to add some other randomness to the setup. Sometimes I spend some of the evening in my office, so let's turn some lights on and off at random:

```yaml
random_office_name: Evening Office
random_office_start: Evening
random_office_end: Night
random_office_minduration: 00:03:00
random_office_maxduration: 00:30:00
random_office_number: 3
random_office_on_1: scene.office_on
random_office_off_1: scene.office_off
```

Here we are using the previous Evening and Night steps as the start and end of the randomness - essentially, after it gets dark but before we finally retire for the night. Each time the light comes on it will stay on for between 3 and 30 minutes, and it will come on 3 times during the evening.

If I had wanted to run the office on its own without the more structured aspects presented above, I would still need to define steps for Evening and Night as the Evening Office event relies on them. They do not need to do anything special however, just define a time. You could do something like the following:

```yaml
step_evening_name: Evening
step_evening_start: sunset - 00:45:00

step_night_name: Night
step_evening_start: 11:00:00
```

This will allow the office randomisations to occur any time between 45 minutes before sunset and 11pm.

# Updating OccuSim

To update OccuSim after I have released new code, just run the following command to update your copy:

```bash
$ git pull origin
```

Then copy occusim.py to your App directory as in the original installation.

# Known Limitations

- It is currently not possible to schedule actions, or allow them to be randomly calculated for the next day. In other words, you had better be in bed and lights out by 12am!
