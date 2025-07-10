# Granada sport backend

## Description

This aim of this app is to publish sport event in a specific city. Users can check the events that will occur in the following days and participate on those events. The app will work as a placeholder for sport enthusiasts. 

This repository contains only backend, and it is done using `FastAPI`. Based on the use cases different endpoints have been created. The app will require user to autheticate to make some actions. 
To persist the data, `Mysql` database will be used. 

## Use cases

* Users
    * Register 
    * Login
    * Update user profile
    * Delete user profile

* Events
    * Create event
    * Modify event
    * Delete event
    * Get user event
    * Get events (all)
    * Participate event
    * Remove event participation

## E-R Diagram 

![E-R Diagram](/granada_sports_ER.png)

## Installation

A docker container has been created, that container contains 2 images: the app itself and mysql image to interact with the database. if you have docker on your PC just execute `docker compose up -d`