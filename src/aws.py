import os
import boto3
from botocore.exceptions import NoCredentialsError


class AWSHandler:
    """
    Handle the functionality when communicating with AWS
    """

    def __init__(self):
        self.auth = boto3.client('s3', aws_access_key_id=os.environ['AWSAccessKeyId'], aws_secret_access_key=os.environ['AWSSecretKey'])

    def upload_image(self, filename: str):
        """
        Upload the current game image to AWS

        :param filename: Name of the file to load and save as on AWS. e.g. user_info.jpg
        """
        filename = filename.split('/')[-1]
        try:
            self.auth.upload_file(f'../extra_files/{filename}', 'clashbotimages', filename,
                                  ExtraArgs={'GrantRead': 'uri=http://acs.amazonaws.com/groups/global/AllUsers'})
        except FileNotFoundError as e:
            print()
            pass
        except NoCredentialsError as e:
            print()
            pass
