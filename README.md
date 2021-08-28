
# Sidekick Assist

Sidekick Assist is a bot built on top of the [Sidekick](https://clashsidekick.com/) bot for Clash of Clans. It uses data pulled by Sidekick and create summary digest for clan feed and clan war feed - this means that you should have already run Sidekick on your sever for your clan for some time. *Data outside this time are not available for analysis.*

 **The bot is still currently under-development**. If you have any questions or want to get in touch, create a post under 'Issues' 

 - **Version**: internal testing
 - **Status**: public bot unavailable
 - **License**: GPL v3

To use this bot, your discord server must have

 - invited Sidekick
 - have some data already generated by Sidekick's clan feed and war feed (depending on which commands/functions you want to use)
 - configure the channels you need Sidekick Assist to access. Details are listed below for each command, but the simplest way is to give the following permissions for every channel you need Sidekick Assist to access:
         - *View channel*
         - *Send messages*
         - *Attach files*
         - *Read message history*
         - *Use Application commands*

You need some Python libraries to run the bot. Import them using the file `discord.yml` in this repository (again the bot is currently not public, so if you are really keen to try it out, get in touch in the Issues section)


## Commands and functions
### ?help
This command lists all comamnds available from Sidekick Assist. Then you can run `?help [command]` to list details on how to use that command

### ?warmiss \[option\] \[from_channel\] \[to_channel\] \[clanname\]
##### NOTE: this command can only be run by the 'admin' role on your discord server

This command sets up the war missed attack feature for your clan. It processes Sidekick war feed, extracts missed attacks at the end of each war, and then post it to another channel. The Sidekick war feed contains a lot of information, which makes it difficult to track missed attacks. This is why we implement this function to extract that information.
 - \[option\]: 
         - **-l**: to list current channel mappings (ignore other parameters when using this option). 
         - **-a**: to add a channel mapping
         - **-r**: to remove a channel mapping
 - \[from_channel\]: this must be the target channel that configured for your Sidekick bot to send your clan's war feed. Sidekick Assist must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want all missed attacks from every war to be posted. Sidekick Assist must have permissions to **View channel**, **Send messages** and **Read message history**
 - \[clanname\]: must be single word without space. This is for output only so it does not have to match your clan name.

#### Examples

`?warmiss -l` 
`?warmiss -a #sidekick-war-feed #war-missed-attacks myclanname`
`?warmiss -r #sidekick-war-feed #war-missed-attacks myclanname` (this mapping should be already added before)

### ?clandigest \[from_channel\] \[to_channel\] \[clan_name]
##### NOTE: this command can be run by everyone

All parameters are mandatory and must not contain space characters. This command is used to summarise Sidekick clan feed in the **current** season. The starting date of the season is extracted from the Sidekick clan feed. 

**Before running this command**, you must run Sidekick command `/best number:50` to create the most recent clan top 50 gainers. This is because Sidekick Assist will need to process that data. 
The command will do the following things:

 - Tally each member's activity count for the current season. This is done by extracting data from Sidekick's clan feed, which include things like: upgrade completion, league promotion, unlocks, super troop boosts, etc. 
 - Tally the clan's total loot (gold, elixir, DE), donations, and raids
 - Outputs all the above data

Parameters:
 - \[from_channel\]: this must be the target channel that configured for your Sidekick bot to send your clan feed. Sidekick Assist must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want the summary to be posted. Sidekick Assist must have permissions to **View channel**, **Send messages** and **Read message history**
 - \[clan_name\]: name of your clan. This does not have to exactly match your clan name.

#### Examples
`?clandigest #clan-feed #target-channel myclanname`

### ?wardigest \[from_channel\] \[to_channel\] \[clan_name] \[dd/mm/yyyy\] \[dd/mm/yyyy\]
##### NOTE: this command can be run by everyone
All parameters except the last one are mandatory and must not contain space characters. This command is used to summarise Sidekick war feed within the two dates provided (when the second is omitted, the current date is used). 

**Before running this command**, you must run Sidekick command `/export ... ` to export war data collected by Sidekick for your clan to a CSV file. This command requires arguments, one of which is the number of the wars from the past. You want to set this to a number that will at least cover the date range defined by the two date arguments. Sidekick Assist will need to process this CSV data. 

**IMPORTANT** if you wish to collect and analyse data for a long period of time it is recommended you run this command multiple times for each month. Collecting data for more than a month at a time can be slow because the bot needs to query Discord for a lot of data. 

The command will do the following things:

 - Tally missed attacks for all members during the date range. 
 - Report the clan's total attacks, total stars gained, and total unused attacks during the date range
 - Creates a stacked bar chart plot to show the clans attack stars against every opponent town hall level, an example is shown below. 
 - Export the raw data as a CSV file
 - Collect individual member's war attack data and save them into a database. These data will be used by the `warpersonal` command (see below). 


Parameters:
 - \[from_channel\]: this must be the channel configured for your Sidekick bot to send your clan's war feed. Sidekick Assist must have permissions to **View channel** and **Read message history**
 - \[to_channel\]: the channel where you want the report to be posted. Sidekick Assist must have permissions to **View channel**, **Send messages**, **Read message history** and **Attach files**
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