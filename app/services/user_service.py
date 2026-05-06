"""
GitHub kullanıcı bilgilerini yöneten servis modülü.
"""
import os
import json
import time
from typing import Dict, List, Any, Optional

class UserService:
    """GitHub kullanıcı bilgilerini yöneten servis sınıfı."""
    
    USER_DATA_DIR = os.path.join("data", "users")
    USER_DATA_FILE = os.path.join(USER_DATA_DIR, "users.json")
    
    @classmethod
    def get_all_users(cls) -> List[Dict[str, Any]]:
        """Tüm kullanıcıları getirir.
        
        Returns:
            List[Dict[str, Any]]: Kullanıcı listesi
        """
        if not os.path.exists(cls.USER_DATA_FILE):
            return []
        
        try:
            with open(cls.USER_DATA_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                return users_data.get("users", [])
        except Exception as e:
            print(f"Kullanıcı verileri okunurken hata oluştu: {str(e)}")
            return []
    
    @classmethod
    def get_user(cls, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı bilgilerini getirir.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            Dict[str, Any]: Kullanıcı bilgileri, bulunamazsa None
        """
        users = cls.get_all_users()
        
        # Kullanıcıyı bul
        for user in users:
            if user.get("username") == username:
                return user
        
        return None
    
    @classmethod
    def add_user(cls, user: Dict[str, Any]) -> bool:
        """Yeni kullanıcı ekler.
        
        Args:
            user: Kullanıcı bilgileri
            
        Returns:
            bool: İşlem başarılı mı
        """
        # Dizini kontrol et
        if not os.path.exists(cls.USER_DATA_DIR):
            os.makedirs(cls.USER_DATA_DIR)
        
        users = cls.get_all_users()
        
        # Kullanıcı zaten var mı kontrol et
        for i, existing_user in enumerate(users):
            if existing_user.get("username") == user.get("username"):
                # Kullanıcıyı güncelle
                users[i] = user
                break
        else:
            # Kullanıcı yoksa ekle
            users.append(user)
        
        # Kullanıcıları kaydet
        try:
            with open(cls.USER_DATA_FILE, "w", encoding="utf-8") as f:
                users_data = {"users": users, "active_user": user.get("username")}
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Kullanıcı verileri kaydedilirken hata oluştu: {str(e)}")
            return False
    
    @classmethod
    def save_user(cls, user: Dict[str, Any]) -> bool:
        """Kullanıcı bilgilerini kaydeder.
        
        Args:
            user: Kullanıcı bilgileri
            
        Returns:
            bool: İşlem başarılı mı
        """
        return cls.add_user(user)
    
    @classmethod
    def remove_user(cls, username: str) -> bool:
        """Kullanıcıyı siler.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            bool: İşlem başarılı mı
        """
        users = cls.get_all_users()
        
        # Kullanıcıyı bul
        for i, user in enumerate(users):
            if user.get("username") == username:
                # Kullanıcıyı sil
                users.pop(i)
                break
        else:
            # Kullanıcı bulunamadı
            return False
        
        # Kullanıcıları kaydet
        try:
            active_user = None
            if users:
                active_user = users[0].get("username")
            
            with open(cls.USER_DATA_FILE, "w", encoding="utf-8") as f:
                users_data = {"users": users, "active_user": active_user}
                json.dump(users_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Kullanıcı verileri kaydedilirken hata oluştu: {str(e)}")
            return False
    
    @classmethod
    def get_default_user(cls) -> Optional[Dict[str, Any]]:
        """Varsayılan kullanıcıyı getirir.
        
        Returns:
            Dict[str, Any]: Varsayılan kullanıcı bilgileri, bulunamazsa None
        """
        if not os.path.exists(cls.USER_DATA_FILE):
            return None
        
        try:
            with open(cls.USER_DATA_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                active_user = users_data.get("active_user")
                
                if not active_user:
                    return None
                
                # Kullanıcıyı bul
                for user in users_data.get("users", []):
                    if user.get("username") == active_user:
                        return user
                
                return None
        except Exception as e:
            print(f"Kullanıcı verileri okunurken hata oluştu: {str(e)}")
            return None
    
    @classmethod
    def set_default_user(cls, username: str) -> bool:
        """Varsayılan kullanıcıyı ayarlar.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            bool: İşlem başarılı mı
        """
        if not os.path.exists(cls.USER_DATA_FILE):
            return False
        
        try:
            with open(cls.USER_DATA_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
            
            # Kullanıcı var mı kontrol et
            for user in users_data.get("users", []):
                if user.get("username") == username:
                    # Varsayılan kullanıcıyı güncelle
                    users_data["active_user"] = username
                    
                    with open(cls.USER_DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(users_data, f, indent=4, ensure_ascii=False)
                    
                    return True
            
            return False
        except Exception as e:
            print(f"Kullanıcı verileri güncellenirken hata oluştu: {str(e)}")
            return False 