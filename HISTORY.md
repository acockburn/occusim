History
=======

1.1.3 (2017-04-14
-----------------

**Features**

None

**Fixes**

- Improved regex for on/off arguments contributed by [Dadeniss](https://github.com/Dadeniss)

**Breaking Changes**

None

1.1.2 (2016-10-02)
------------------

**Features**

None

**Fixes**

- Changes test mode to only activate when test is set to "1". Setting it to any other value, e.g. "0" or omiting it will disable test mode.

**Breaking Changes**

- Test mode will no longer be enabled for values of the parameter test other than "1"

None

1.1.1 (2016-10-02)
------------------

**Features**

None

**Fixes**

- Fixed a bug where custome events were not honoring test mode

**Breaking Changes**

None

1.1.0 (2016-10-01)
------------------

**Features**

- Steps can now fire arbitrary number of Home Assistant Events
- Day constraints are now applied per step not globally
- An arbitrary number of input_select can be set for each step instead of a single global input_select

**Fixes**

- None

**Breaking Changes**

- input_select changes are now specified per step
- day constraints are no longer global and have to be specified per step

1.0.0 (2016-09-16)
------------------

**Initial Release**
