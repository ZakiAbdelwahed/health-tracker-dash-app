# Health Tracker Dashboard
<img src="https://github.com/ZakiAbdelwahed/health-tracker-dash-app/blob/main/Readme%20images/oura%20logo.jpg" style="float:left;width:40%;height:40%;"> <img src="https://github.com/ZakiAbdelwahed/health-tracker-dash-app/blob/main/Readme%20images/apple%20logo.png" style="float:right;width:40%;height:40%;">

App: https://my-personal-health-tracker.onrender.com/

## 1. Goal
One my goals in life is to live to 100 in the best mental and physical shape possible.

Thanks to health tracking devices, we now have access to an array of biometric data on a daily basis. While these devices may not be perfect, they can still give us an idea of our overall health trends. Personally, I use an Oura ring and an Apple Watch. Both devices have great apps with dashboards and graphs, but I wanted to have all my data in one place and add additional graphs. For example, the Oura ring estimates how much REM and deep sleep I get per night, but the app doesn't offer the possibility to see how that amount is evolving over time.

Another one of my goals is to run the equivalent of the earth's circumference, this dashboard helps me track my progress (Spoiler alert: I still have a long way to go :wink: :running:)

## 2. Data displayed
- Average HRV
- Average lowest heart rate
- Average total sleep duration
- VO2 max
- Number of kilometers run since October 2016
- HRV trend
- Zone 2 performance trend
- VO2 max trend
- Total sleep trend
- Deep sleep vs REM sleep
- Deep sleep trend
- REM sleep trend

## 2. Definitions
**HRV**: HRV stands for Heart Rate Variability. It is a measure of the variation in time between successive heartbeats. It is often used as a marker of the nervous system's balance between the sympathetic (fight or flight) and parasympathetic (rest and digest) branches. HRV can be used to indicate how well the body is adapting to stressors and to assess the overall health of the autonomic nervous system.

**VO2 max**: VO2 max is a measure of the maximum amount of oxygen that a person can consume during intense exercise. It is often used as a measure of cardiovascular fitness and can be improved through training.

**Zone 2**: Zone 2 training is a type of exercise training that involves maintaining a blood lactate concentration of less than 2 mmol which is typically between 60-70% of your maximum heart rate. This type of training is often used for endurance and cardiovascular fitness.

**Deep sleep**: Deep sleep, also known as slow-wave sleep, is a stage of the sleep cycle where the brain activity slows down and the body is in a state of deep relaxation. During deep sleep, the body repairs and rejuvenates itself, including the growth and development of cells, tissues, and muscles. Hormones are released during this stage that help with memory consolidation, immune system function, and other vital processes. It is considered the most restorative stage of sleep and is essential for overall physical and mental health.

**REM sleep**: REM sleep stands for Rapid Eye Movement sleep, it is a stage of the sleep cycle characterized by rapid eye movement, increased brain activity, and vivid dreaming. During REM sleep, the brain is highly active and the body is in a state of paralysis, this is to prevent the person from acting out their dreams. This stage of sleep is important for memory consolidation, emotional regulation, and learning. The first REM episode usually begins about 90 minutes after falling asleep and lasts for about 10 minutes, but as the night progresses, REM episodes can last up to an hour and occur more frequently.

## 3. Tools
- [Oura's API](https://cloud.ouraring.com/v2/docs)
- [Health Export CSV app](https://apps.apple.com/us/app/health-export-csv/id1477944755)
- [Google Drive's API](https://developers.google.com/drive)
- [Dash](https://dash.plotly.com/)
- [Render](https://render.com/)

## 4. Improvements

**Apple Health data:** Collecting data directly from Apple Health proved to be challenging for me, so I chose to use the [Health Export CSV app](https://apps.apple.com/us/app/health-export-csv/id1477944755) to simplify the process. The app collects and exports the data as a CSV file, which I then upload to my Google Drive and connect to the dashboard using the API. This method could be optimized to eliminate the manual steps of downloading and uploading files. 

**Responsiveness:** The annotations I added to the graphs are not responsive. Additionally, the display of the graphs on mobile devices is only functional when the phone is held horizontally. These are two issues that I am currently unable to explain or resolve.

**Performance:** The loading time of the graphs on the dashboard is excessive, taking approximately 10-15 seconds. I need to investigate the source of the delay, whether it is related to Dash or Render.

## 4. Next step
The next step is to implement tracking of my blood work results by uploading PDF files, which will enable me to monitor each biomarker over time.

## 5. Ressources
- [Downloading and uploading files to Google drive using python](https://www.youtube.com/watch?v=Z2kfNx3Cgsk)
- [Dash tutorials](https://www.youtube.com/c/charmingdata)
- [Fontawesome icons](https://fontawesome.com/v4/icons/)
