#imports the whole app into this page
#this is so it can all be run at once
from website import create_app

#function is established
app = create_app()

#the code is set to debugging mode
#this is for development purposes
#as changes can be made live
#without having to restart the application
if __name__ == '__main__':
    app.run(debug=True)
