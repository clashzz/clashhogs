

# Clash Hogs

Clash Hogs is a bot for **Clash of Clans**. It implements a few handy utilities for analysing clan data, and making clan management easier. 

 **The bot is under-development**. If you have any questions or want to get in touch, create a post under 'Issues' 

 - **Version**: internal deployment
 - **Status**: public bot unavailable
 - **License**: GPL v3

**To use this bot**, your discord server must 
 - configure the channels you need Clash Hogs to access. Details are listed below for each command, but the simplest way is to give the following permissions for every channel you need Clash Hogs to access:
     - *View channel*
     - *Send messages*
     - *Attach files*
     - *Read message history*
     - *Use Application commands*

**To start the bot**

 - Make sure you have Python 3.9, and you also need a Discord API token and a Clash of Clans API account
 - Install required libraries using the file `discord.yml` in this repository (again the bot is currently not public, so if you are really keen to try it out, get in touch in the Issues section)
 - Set up your environment file under  `env/.env`. See the file `template.env` for example
 - Run the `bot.py` file under `src`. E.g.: `export PYTHONPATH=/path/to/the/src/ 
python3 -m skassist.bot [path to the env folder]`


## Commands and functions
### ?help
This command lists all comamnds available from Clash Hogs. Then you can run `?help [command]` to list details on how to use that command

### ?warmiss \[option\] \[from_channel\] \[to_channel\] \[clanname\]
##### NOTE: this command can only be run by the 'admin' role on your discord server

This command sets up the war missed attack feature for your clan. It processes Sidekick war feed, extracts missed attacks at the end of each war, and then post it to another channel. The Sidekick war feed contains a lot of information, which makes it difficult to track missed attacks. This is why we implement this function to extract that information.
 - \[option\]: 
     - **-l**: to list current channel mappings (ignore other parameters when using this option). 
     - **-a**: to add a channel mapping
     - **-r**: to remove a channel mapping
 - \[from_channel\]: this must be the target channel that configured for your Sidekick bot to send your clan's war feed. Clash Hogs must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want all missed attacks from every war to be posted. Clash Hogs must have permissions to **View channel**, **Send messages** and **Read message history**
 - \[clanname\]: must be single word without space. This is for output only so it does not have to match your clan name.

#### Examples

`?warmiss -l` 
`?warmiss -a #sidekick-war-feed #war-missed-attacks myclanname`
`?warmiss -r #sidekick-war-feed #war-missed-attacks myclanname` (this mapping should be already added before)

### ?clandigest \[from_channel\] \[to_channel\] \[clan_name]
##### NOTE: this command can be run by everyone

All parameters are mandatory and must not contain space characters. This command is used to summarise Sidekick clan feed in the **current** season. The starting date of the season is extracted from the Sidekick clan feed. 

**Before running this command**, you must run Sidekick command `/best number:50` to create the most recent clan top 50 gainers. This is because Clash Hogs will need to process that data. 
The command will do the following things:

 - Tally each member's activity count for the current season. This is done by extracting data from Sidekick's clan feed, which include things like: upgrade completion, league promotion, unlocks, super troop boosts, etc. 
 - Tally the clan's total loot (gold, elixir, DE), donations, and raids
 - Outputs all the above data

Parameters:
 - \[from_channel\]: this must be the target channel that configured for your Sidekick bot to send your clan feed. Clash Hogs must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want the summary to be posted. Clash Hogs must have permissions to **View channel**, **Send messages** and **Read message history**
 - \[clan_name\]: name of your clan. This does not have to exactly match your clan name.

#### Examples
`?clandigest #clan-feed #target-channel myclanname`

### ?wardigest \[from_channel\] \[to_channel\] \[clan_name] \[dd/mm/yyyy\] \[dd/mm/yyyy\]
##### NOTE: this command can be run by everyone
All parameters except the last one are mandatory and must not contain space characters. This command is used to summarise Sidekick war feed within the two dates provided (when the second is omitted, the current date is used). 

**Before running this command**, you must run Sidekick command `/export ... ` to export war data collected by Sidekick for your clan to a CSV file. This command requires arguments, one of which is the number of the wars from the past. You want to set this to a number that will at least cover the date range defined by the two date arguments. Clash Hogs will need to process this CSV data. 

**IMPORTANT** if you wish to collect and analyse data for a long period of time it is recommended you run this command multiple times for each month. Collecting data for more than a month at a time can be slow because the bot needs to query Discord for a lot of data. 

The command will do the following things:

 - Tally missed attacks for all members during the date range. 
 - Report the clan's total attacks, total stars gained, and total unused attacks during the date range
 - Creates a stacked bar chart plot to show the clans attack stars against every opponent town hall level, an example is shown below. 
 - Export the raw data as a CSV file
 - Collect individual member's war attack data and save them into a database. These data will be used by the `warpersonal` command (see below). 


Parameters:
 - \[from_channel\]: this must be the channel configured for your Sidekick bot to send your clan's war feed. Clash Hogs must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want the report to be posted. Clash Hogs must have permissions to **View channel**, **Send messages**, **Read message history** and **Attach files**
 - \[clan_name\]: name of your clan. This does not have to exactly match your clan name.
 - \[dd/mm/yyyy\]: the first is the starting date of the range. The second is the end date of the range (when omitted, the current date will be used). Data within the date range will be collected and analysed. Therefore, when you run the Sidekick command `/export ... ` make sure you export enough data covering this date range.

#### Examples
`?wardigest #war-log #target-channel myclanname 26/05/2021 26/06/2021`

### ?warpersonal \[player_tag\] \[dd/mm/yyyy\] \[dd/mm/yyyy\]
##### NOTE: this command can be run by everyone
All parameters except the last one are mandatory and must not contain space characters. This command is used to summarise war performance for an individual player. The war data are collected as part of the process of running `wardigest`. This means you should have run `wardigest`for the past months to populate personal war data for this command to work.

The command will do the following things:

 - Creates a stacked bar chart plot to show the player's attack stars against every opponent town hall level.
 - Creates a grouped bar chart to show the players attack stars (0, 1, 2, 3) over different months

Parameters:
 - \[player_tag\]: this must be the player's tag (including #). Note that as the data are generated by running `wardigest`, the player must have already been a member and took part in war in the clan for the date range in question.
 - \[dd/mm/yyyy\]: the first is the starting date of the range. The second is the end date of the range (when omitted, the current date will be used). Data within the date range will be collected and analysed. 

#### Examples
`?warpersonal #ke09sdkl 26/05/2021 26/06/2021`

### ?warn \[option\] \[clanname] \[playername\] \[value\] \[note\]
##### NOTE: this command can only be run by users with administrator access
This command is used to record warnings for a clan member. Options:

 - -l: to list all warnings of a clan, or a player in a clan (clanname is mandatory, other parameters can be ignored). E.g., `?warn -l MyClan` , `?warn -l MyClan playername1`
 - -a: to add a warning for a player of a clan, and assign a value to that warning (all parameters mandatory except note, which can be multi-word but must be the last parameter). E.g., `?warn -a MyClan playername1 1.5 missing one CWL attack`
 - -c: to remove all warnings of a player in a clan (clanname and playername mandatory). E.g., `?warn -c MyClan playername1`
 -  -d: to delete a specific warning record or a set of records. You can delete records in two ways.
   - Delete a single record: provide [clanname] and an ID of the record to replace [playername]. If the ID and the provided clan name do not match existing records in the database, no records will be deleted. E.g., `warn -d MyClan 1`
   - Delete a set of records before a certain date: this will delete ALL records earlier than a date you provide, in the format of YYYY-MM-DD (time is set to be 00h 00m 00s). E.g., `warn -d MyClan 2021-12-31` will delete ALL warning records entered before 2021 Dec 31

### ?crclan \[option\] \[clantag] \[*value\]  
##### NOTE: this command can only be run by users with administrator access
This command is used to **set up a clan** for the 'credit watch' system. Credit watch is a system that gives/reduces credits for members for certain actions, such as using/missing an attack in a war. This command is for setting up the system for a clan so that the following activities are monitored and credits registered automatically:

 - Using an attack in a regular war (cw_attack)
 - Missing an attack in a regular war (cw_miss)
 - Using an attack in a CWL war (cwl_attack)
 - Missing an attack in a CWL war (cwl_miss)

**Friendly wars are excluded**. Since the monitoring depends on the Clash of Clans API's 'events', currently these are the only activities that can be monitored automatically. Other activities (e.g., clan game no. 1, donation no. 1) must be credited manually (see below the `crplayer` command.

Options:
 - -l: List clans currently registered for the credit system. The result will list the credits configured for each of the four events above. If [clantag] is supplied, only that clan will be shown. E.g., `crclan -l #SOMETAG`. If you want to see all registered clans, use `crclan -l *`
 -  -a: To register a clan for credit watch. [clantag] is mandatory. Other multiple [value] parameters can specify the credit points and events to be registered. If none provided, then default as: _cw_attack=10 cw_miss=-10 cwl_attack=10 cwl_miss=-10_. If you want to customise the values, provide them in the same format as above, each separated by a whitespace. E.g. `crclan -a #SOMETAG cw_attack=10 cw_miss=-10 cwl_attack=15 cwl_miss=-15`. As a result of this, if a member uses an attack in a regular war, s/he is credited 10 points; if s/he misses a cwl attack, s/he loses 15 points.
 - -d: to remove a clan from credit watch. [clantag is mandatory]. E.g., `crclan -d #SOMETAG`

##### IMPORTAT: each time you run this command with the `-a` option for the same clan, the credit settings will replace the previous ones. And they will ONLY apply to future events, not the prevoius ones.
##### IMPORTAT: automated war credits are calculated at the END of each war, not immediately after an attack event takes place.

### ?crplayer \[option\] \[tag] \[value\] \[note\] 
##### NOTE: this command can only be run by users with administrator access
This command is used to manage credits of **individual players**. You can use this command to view, add or delete credits manually to a player. 

Options:
 - -lc: List all players's total credits in a clan, specified by the [tag] (must be a clan tag). E.g., `crplayer -lc #CLANTAG`. The result will show the total credits of each member in the clan. For each individual credit record, see below 
 - -lp: List a specific player's credit records in a clan, specified by the [tag] (must be a player tag). E.g., `crplayer -lp #PLAYERTAG`. The result will show each credit record of this player, The time, points, and reasons will be shown. 
 - -a: To manually add credits of [value] to a player specified by the [tag] (must be a player tag). When using this command, you must also provide a reason [note] (can be a sentence). E.g., `crplayer -a #PLAYERTAG 30 Clan game no. 1`
 - -d: To delete credits for all players of a clan, specified by the [tag] (confirmation required). Warning: this will delete ALL records for the clan. Confirmation will be required


<img src="https://ibb.co/GHz34MP" alt="MarineGEO circle logo" style="height: 100px; width:100px;"/>
