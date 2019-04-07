# sinzlab-tools

## Setup

1. Clone this repository:

    ``git clone https://github.com/cblessing24/sinzlab-tools.git``
    
2. Change your current working directory:

    ``cd ./sinzlab-tools``

3. Build the docker image:

    ``docker build -t sinzlab-tools .``
    
4. Create a `.env` file and add the following lines to it:

    ``USER=myusername``  
    ``PASS=mypassword``

## Usage

You can access the cli with the following command:

``docker run --rm --env-file .env --entrypoint sinzlab_tools sinzlab-tools``