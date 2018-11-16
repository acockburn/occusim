import appdaemon.plugins.hass.hassapi as hass
import datetime
import re
import random
import pytz

#
# App to simulate occupancy in an empty house
#

__version__ = "1.1.5"


class OccuSim(hass.Hass):

    def initialize(self):

        if "test" in self.args and self.args["test"] == "1":
            self.test = True
        else:
            self.test = False

        if "local_tz" in self.args:
            self.local_tz = pytz.timezone(self.args["local_tz"])
        else:
            self.local_tz = None
        
        if "system_tz" in self.args:
            self.system_tz = pytz.timezone(self.args["system_tz"])
        else:
            self.system_tz = pytz.timezone("UTC")

        self.timers = ()

        # Set a timer to recreate the day's events at 3am
        if "reset_time" in self.args:
            time = self.parse_time(self.args["reset_time"])
        else:
            time = datetime.time(3, 0, 0)
        self.run_daily(self.create_events, time)

        # Create today's random eventspytz
        self.create_events({})

    def create_events(self, kwargs):
        # self.log_notify("Running Create Events")

        events = {}
        steps = ()
        randoms = ()

        for arg in self.args:
            m = re.search("step_(.+)_name", arg)
            if m:
                steps = steps + (m.group(1),)
            m = re.search("random_(.+)_name", arg)
            if m:
                randoms = randoms + (m.group(1),)

        # First pick up absolute events
        for step in steps:
            event = None
            step = "step_" + step + "_"
            if (step + "start") in self.args:
                stepname = self.args[step + "name"]
                cbargs = {}
                cbargs["step"] = stepname
                if (step + "days") in self.args:
                    cbargs["days"] = self.args[step + "days"]
                span = 0
                for arg in self.args:
                    if re.match(step + "on", arg) or re.match(step + "off", arg):
                        cbargs[arg] = self.args[arg]
                
                start_p = self.args[step + "start"]
                start = self.parse_time(start_p)
                end_p = self.args.get(step + "end")

                mask = start_p
                if end_p != None:
                    end = self.parse_time(end_p)
                    start_ts = datetime.datetime.combine(self.local_date(), start).timestamp()
                    end_ts = datetime.datetime.combine(self.local_date(), end).timestamp()
                    span = int(end_ts - start_ts)
                    mask += end_p
                if span == 0:
                    event = datetime.datetime.combine(self.local_date(), start)
                else:
                    if span < 0:
                        span = self.after_midnight(span, step)
                    event = datetime.datetime.combine(self.local_date(), start) + datetime.timedelta(
                        seconds=random.randrange(span))
                if not (re.match(r'[^\d:]', mask)): # If label or text present, already in UTC
                    event = self.to_system_tz(event) # Else, convert time to UTC

                events[stepname] = {}
                events[stepname]["event"] = event
                events[stepname]["args"] = cbargs.copy()

        # Now relative events - multiple passes required as the order could be arbitrary

        changes = 1

        while changes > 0:
            changes = 0
            for step in steps:
                event = None
                step = "step_" + step + "_"
                if (step + "relative") in self.args:
                    stepname = self.args[step + "name"]
                    if stepname not in events:
                        cbargs = {}
                        cbargs["step"] = stepname
                        if (step + "days") in self.args:
                            cbargs["days"] = self.args[step + "days"]
                        span = 0
                        for arg in self.args:
                            if re.match(step + "on", arg) or re.match(step + "off", arg):
                                cbargs[arg] = self.args[arg]

                        steprelative = self.args[step + "relative"]
                        if steprelative in events:
                            start_offset_p = self.args[step + "start_offset"]
                            start_offset = self.parse_time(start_offset_p)
                            start = events[steprelative]["event"] + datetime.timedelta(hours=start_offset.hour,
                                                                                       minutes=start_offset.minute,
                                                                                       seconds=start_offset.second)
                            end_offset_p = self.args.get(step + "end_offset")
                            if end_offset_p != None:
                                end_offset = self.parse_time(end_offset_p)
                                end = events[steprelative]["event"] + datetime.timedelta(hours=end_offset.hour,
                                                                                         minutes=end_offset.minute,
                                                                                         seconds=end_offset.second)
                                span = int(end.timestamp() - start.timestamp())
                            if span == 0:
                                event = start
                            else:
                                if span < 0:
                                    self.after_midnight(span, step)
                                event = start + datetime.timedelta(seconds=random.randrange(span))

                            events[stepname] = {}
                            events[stepname]["event"] = event
                            events[stepname]["args"] = cbargs.copy()
                            changes += 1

        list = ""
        for step in steps:
            stepname = self.args["step_" + step + "_name"]
            if stepname not in events:
                list += stepname + " "

        if list != "":
            self.log("unable to schedule the following steps due to missing prereq step: {}".format(list), "WARNING")

        # Schedule random events

        for step in randoms:
            event = None
            step = "random_" + step + "_"
            stepname = self.args[step + "name"]
            cbonargs = {}
            cboffargs = {}
            if (step + "days") in self.args:
                cbonargs["days"] = self.args[step + "days"]
                cboffargs["days"] = self.args[step + "days"]

            span = 0
            for arg in self.args:
                if re.match(step + "on", arg):
                    cbonargs[arg] = self.args[arg]
                if re.match(step + "off", arg):
                    cboffargs[arg] = self.args[arg]

            startstep = self.args[step + "start"]
            endstep = self.args[step + "end"]
            starttime = events[startstep]["event"]
            endtime = events[endstep]["event"]
            tspan = int(endtime.timestamp() - starttime.timestamp())
            if tspan < 0:
                tspan = self.after_midnight(tspan, step)

            mind_p = self.args[step + "minduration"]
            mind = self.parse_time(mind_p)
            mindts = datetime.datetime.combine(self.local_date(), mind).timestamp()
            maxd_p = self.args[step + "maxduration"]
            maxd = self.parse_time(maxd_p)
            maxdts = datetime.datetime.combine(self.local_date(), maxd).timestamp()
            dspan = int(maxdts - mindts)
            minds = (mind.hour * 60 + mind.minute) * 60 + mind.second
            maxds = (maxd.hour * 60 + maxd.minute) * 60 + maxd.second
            numevents = int(self.args[step + "number"])
            
            times_on = [random.randint(minds, maxds) for i in range(numevents)]
            times_on_sum = sum(times_on)
            
            while times_on_sum > tspan:
                times_on[times_on.index(max(times_on))] = minds
                times_on_sum = sum(times_on)
        
            spaceleft = tspan - times_on_sum
            spaces = [dspan * random.random() + 1 for i in range(numevents + 1)]
            spaces = [int(s * spaceleft / sum(spaces)) for s in spaces]
            
            if sum(spaces) != spaceleft:
                diff = sum(spaces) - spaceleft
                if sum(spaces) > spaceleft:
                    spaces[spaces.index(max(spaces))] -= diff
                else:
                    spaces[spaces.index(min(spaces))] -= diff
                    
            turn_on = []
            turn_off = []
            times_on = [datetime.timedelta(seconds = s) for s in times_on]
            spaces = [datetime.timedelta(seconds = s) for s in spaces]
            
            if not re.match(r'[^\d:]', startstep): # If label or text present, already in UTC
                starttime = self.to_system_tz(starttime) # Else, convert time to UTC
            turn_on.insert(0, starttime + spaces[0])
            turn_off.insert(0, turn_on[0] + times_on[0])
            
            for i in range(1, numevents):
                turn_on.insert(i, turn_off[i - 1] + spaces[i])
                turn_off.insert(i, turn_on[i] + times_on[i])

            for i in range(numevents):
                eventname = stepname + "_on_" + str(i)
                events[eventname] = {}
                events[eventname]["event"] = turn_on[i]
                cbonargs["step"] = eventname
                events[eventname]["args"] = cbonargs.copy()

                eventname = stepname + "_off_" + str(i)
                events[eventname] = {}
                events[eventname]["event"] = turn_off[i]
                cboffargs["step"] = eventname
                events[eventname]["args"] = cboffargs.copy()

        # Take all the events we found and schedule them

        for event in sorted(events.keys(), key=lambda event: events[event]["event"]):
            stepname = events[event]["args"]["step"]
            start = events[event]["event"]
            args = events[event]["args"]
            if start > self.datetime():
                # schedule it
                if "enable" in self.args:
                    args["constrain_input_boolean"] = self.args["enable"]
                if "select" in self.args:
                    args["constrain_input_select"] = self.args["select"]
                if "days" in events[event]["args"]:
                    args["constrain_days"] = events[event]["args"]["days"]
                self.run_at(self.execute_step, start, **args)
                if "dump_times" in self.args:
                    self.log("{}: @ {}".format(stepname, self.to_local_tz(start)))
            else:
                self.log("{} in the past - {} ignoring".format(stepname, self.to_local_tz(start)))

    def execute_step(self, kwargs):
        # Set the house up for the specific step
        self.step = kwargs["step"]
        self.log_notify("Executing step {}".format(self.step))
        for arg in kwargs:
            if re.match(".+_on_.+", arg):
                self.activate(kwargs[arg], "on")
            elif re.match(".+_off_.+", arg):
                self.activate(kwargs[arg], "off")

    def activate(self, entity, action):
        type = action
        m = re.match(r'event\.(.+)\,(.+)', entity)
        if m:
            if not self.test: self.fire_event(m.group(1), **{m.group(2): self.step})
            if "log" in self.args:
                self.log("fired event {} with {} = {}".format(m.group(1), m.group(2), self.step))
            return
        m = re.match(r'input_select\.', entity)
        if m:
            if not self.test: self.select_option(entity, self.step)
            self.log("set {} to value {}".format(entity, self.step))
            return
        if action == "on":
            if not self.test: self.turn_on(entity)
        else:
            if re.match(r'scene\.', entity) or re.match(r'script\.', entity):
                type = "on"
                if not self.test: self.turn_on(entity)
            else:
                if not self.test: self.turn_off(entity)

        if "log" in self.args:
            self.log("turned {} {}".format(type, entity))

    def log_notify(self, message):
        if "log" in self.args:
            self.log(message)
        if "notify" in self.args:
            self.notify(message)
    
    def after_midnight(self, time, step):
        time += 86400
        self.log("{}end < {}start - assuming end is midnight or later".format(step, step))
        return time

    def to_system_tz(self, dt):
        if self.local_tz != None:
            localtime = self.local_tz.localize(dt)
            return localtime.astimezone(self.system_tz).replace(tzinfo = None)
        else:
            return dt
            
    def to_local_tz(self, dt):
        if self.local_tz != None:
            systemtime = self.system_tz.localize(dt)
            return systemtime.astimezone(self.local_tz).replace(tzinfo = None)
        else:
            return dt

    def local_date(self):
        system_date = self.date()
        if self.local_tz != None:
            system_datetime = datetime.datetime.combine(system_date, self.time())
            return self.to_local_tz(system_datetime).date()
        else:
            return system_date
