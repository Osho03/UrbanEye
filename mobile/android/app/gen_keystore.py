import subprocess
import os

def generate_keystore():
    keytool_path = r"C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe"
    cmd = [
        keytool_path, "-genkey", "-v",
        "-keystore", "urbaneye-key.jks",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-alias", "urbaneye",
        "-storepass", "urbaneye_pass",
        "-keypass", "urbaneye_pass",
        "-dname", "CN=UrbanEye, OU=Engineering, O=UrbanEye, L=City, ST=State, C=IN",
        "-noprompt"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="d:/UrbanEye/mobile/android/app")
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if os.path.exists("d:/UrbanEye/mobile/android/app/urbaneye-key.jks"):
        print("✅ Keystore generated successfully!")
    else:
        print("❌ Keystore generation failed!")

if __name__ == "__main__":
    generate_keystore()
