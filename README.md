# certsnake

Renew or create a Lets Encrypt certifcate for each CNAME and A record in AWS route 53. 
If the certificates are not up for renewal there will be no certificates output. 

### Requirements
* Ubuntu 20.0.4
* AWS account with the correct access policy attached
    * https://certbot-dns-route53.readthedocs.io/en/stable/

### Installation instructions 

* install python venv
  
        sudo apt install python3-venv -y
  
* Clone repository  

        git clone https://github.com/chet-space/certsnake.git

* Create python venv
  
        cd certsnake && python3 -m venv venv

* Activate venv

        source venv/bin/activate  
  
* install requirements
  
        pip3 install pip --upgrade
        pip3 install -r requirements.txt

* Install AWS cli
    * https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html
      
              sudo apt install unzip  
              curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
              unzip awscliv2.zip
              sudo ./aws/install

* Add your Route53 HostedZoneId to configuration.py
* Update email and other options at cli.ini  
* Create AWS credential file

        aws configure

* run script

        python3 main.py

* certificates are output to: 
  
        /archive/<domain-name>/
        symlinks --> config/<domain-name>/live/<domain-name>/
