import os
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.bucket = settings.SUPABASE_BUCKET
        
        # We initialize the client inside the methods or here
        self.client: Client = create_client(
            self.supabase_url, 
            self.supabase_key,
            # We don't need realtime or postgrest for storage, but default options are fine
        )

    def _open(self, name, mode='rb'):
        # Download the file from Supabase
        res = self.client.storage.from_(self.bucket).download(name)
        return ContentFile(res)

    def _save(self, name, content):
        file_bytes = content.read()
        content_type = getattr(content, "content_type", "application/octet-stream")
        
        # Ensure path uses forward slashes
        name = str(name).replace('\\', '/')
        
        self.client.storage.from_(self.bucket).upload(
            file=file_bytes,
            path=name,
            file_options={"content-type": content_type}
        )
        return name

    def exists(self, name):
        # Supabase Python SDK doesn't have a direct 'exists' check without fetching metadata/listing.
        # A simple way is to try generating a public URL and assume it exists if we are asking.
        # But for Django, exists() is used to prevent overwriting. 
        # Supabase will throw an error on upload if it already exists, unless upsert is true.
        # Let's return False and let Supabase handle conflicts or we can do a list check.
        try:
            # We list the directory and see if the file is in it
            path_parts = name.split('/')
            file_name = path_parts[-1]
            folder_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''
            
            res = self.client.storage.from_(self.bucket).list(folder_path)
            for file_info in res:
                if file_info.get('name') == file_name:
                    return True
            return False
        except Exception:
            return False

    def url(self, name):
        # Return a signed URL valid for 1 hour (3600 seconds) since the bucket is private
        name = str(name).replace('\\', '/')
        res = self.client.storage.from_(self.bucket).create_signed_url(name, 3600)
        return res.get('signedURL')

    def delete(self, name):
        name = str(name).replace('\\', '/')
        self.client.storage.from_(self.bucket).remove([name])
        
    def size(self, name):
        try:
            path_parts = name.split('/')
            file_name = path_parts[-1]
            folder_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''
            
            res = self.client.storage.from_(self.bucket).list(folder_path)
            for file_info in res:
                if file_info.get('name') == file_name:
                    return file_info.get('metadata', {}).get('size', 0)
            return 0
        except Exception:
            return 0
