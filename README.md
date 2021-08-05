# ChairDetector
Program that notifies the user when a Herman Miller chair ad is posted on Kijiji whose price is under a user specified threshold. 

Before Use:
  1. Download model.pt from Latest Release and store in detector folder
  2. Install Selenium Chrome WebDriver (Must have Chrome Browser installed)
  3. pip install any required python libraries
  4. Run init.py file, this will initialize the program
  5. In scanner/notifier.py, change the DRIVER_LOC constant to be the location of your Selenium Chrome WebDriver

To Use:
  1. From the ChairDetector directory, run scanner/notifier.py
  2. A cronjob can be implemented to run the program on a schedule.
