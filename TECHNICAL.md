# Technical Preferences
* Frontend: This can be entirely static html as we're merely listing out links to RSS feeds. If we decide in the future, say to add ability to select an avalanche center then display the zones, then try to build this with vanilla JS. If that doesn't work, bring in simple libraries. Don't adopt a large dependency like React.
* Backend: 
* Backend: Python using Flask, setup to hot reload on changes. Use a modern version of Python. If one isn't available, call this out before and suggest a version.
* Database: None Needed
* Task Processing: None Needed
* Object storage: initial the file system, in a future iteration, we'll use S3.

# Development Tooling:
* Python environment via VirtualEnv
* Python depedencies managed via requirements.txt
* CI via Github Actions. Actions shouldn't have code/logic embedded in them. Actions should invoke shell script(s). The goal here is to ensure the action can be executed locally.
* The application should find secrets via environment varaibles. For development, these should be stored in an .env file, and a program or library used to make these available.
