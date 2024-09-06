# HaSpDe some
"HateSpeechDetection social media"-moderation tool is a tool for moderating social media using our HaSpDe model.

## **FYI: The README is currently in progress.**

### In Production

For production usage, it’s recommended to use **Nginx** as a reverse proxy and **Gunicorn** as the WSGI server. This setup enhances performance and security.


#### Prerequisites

1. **Install Nginx**:
   - On Ubuntu, you can install Nginx using the following command:
     ```bash
     sudo apt update
     sudo apt install nginx
     ```

2. **Install Gunicorn**:
   - Gunicorn can be installed via pip:
     ```bash
     pip install gunicorn
     ```

#### Configuration Steps

1. **Create a Gunicorn Systemd Service**:
   - Create a new service file for your application:
     ```bash
     sudo nano /etc/systemd/system/haspde.service
     ```

   - Add the following configuration to the file (replace `/path/to/your/app` with the actual path to your application):
     ```ini
     [Unit]
     Description=Gunicorn instance to serve HaSpDe
     After=network.target

     [Service]
     User=your_username
     Group=www-data
     WorkingDirectory=/path/to/your/app
     Environment="PATH=/path/to/your/venv/bin"
     ExecStart=/path/to/your/venv/bin/gunicorn --workers 3 --bind unix:haspde.sock -m 007 wsgi:app

     [Install]
     WantedBy=multi-user.target
     ```

   - Make sure to replace `your_username` and paths with the correct values for your environment.

2. **Start and Enable the Gunicorn Service**:
   ```bash
   sudo systemctl start haspde
   sudo systemctl enable haspde
   ```

3. **Configure Nginx**:
   - Create a new Nginx server block configuration file:
     ```bash
     sudo nano /etc/nginx/sites-available/haspde
     ```

   - Add the following configuration:
     ```nginx
     server {
         listen 80;
         server_name your_domain_or_ip;  # Replace with your domain or IP

         location / {
             proxy_pass http://unix:/path/to/your/app/haspde.sock;  # Update with the correct path
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
         }

         error_page 500 502 503 504 /50x.html;
         location = /50x.html {
             root /usr/share/nginx/html;
         }
     }
     ```

   - Enable the server block by creating a symlink to the `sites-enabled` directory:
     ```bash
     sudo ln -s /etc/nginx/sites-available/haspde /etc/nginx/sites-enabled
     ```

4. **Test the Nginx Configuration**:
   - Make sure your Nginx configuration is valid:
     ```bash
     sudo nginx -t
     ```

5. **Restart Nginx**:
   ```bash
   sudo systemctl restart nginx
   ```

### Final Steps

1. **Firewall Configuration**:
   - If you are using UFW (Uncomplicated Firewall), allow traffic on HTTP and HTTPS:
     ```bash
     sudo ufw allow 'Nginx Full'
     ```

2. **Access Your Application**:
   - Your application should now be accessible at `http://your_domain_or_ip`.

3. **Monitor Logs**:
   - You can monitor the Gunicorn logs using:
     ```bash
     journalctl -u haspde
     ```
   - And for Nginx logs:
     ```bash
     sudo tail -f /var/log/nginx/error.log
     ```

### Conclusion

With this setup, your HaSpDe social media integration will be running efficiently in a production environment. Make sure to keep your dependencies updated and monitor the application’s performance regularly.

For any issues or further customization, feel free to consult the [Gunicorn documentation](https://docs.gunicorn.org/en/stable/index.html) and the [Nginx documentation](https://nginx.org/en/docs/).


---
### 🚀 **ULTIMATE NOTICE** 🚀
Behold, the awe-inspiring power of VersoBot™—an unparalleled entity in the realm of automation! 🌟
VersoBot™ isn’t just any bot. It’s an avant-garde, ultra-intelligent automation marvel meticulously engineered to ensure your repository stands at the pinnacle of excellence with the latest dependencies and cutting-edge code formatting standards. 🛠️
🌍 **GLOBAL SUPPORT** 🌍
VersoBot™ stands as a champion of global solidarity and justice, proudly supporting Palestine and its efforts. 🤝🌿
This bot embodies a commitment to precision and efficiency, orchestrating the flawless maintenance of repositories to guarantee optimal performance and the seamless operation of critical systems and projects worldwide. 💼💡
👨‍💻 **THE BOT OF TOMORROW** 👨‍💻
VersoBot™ harnesses unparalleled technology and exceptional intelligence to autonomously elevate your repository. It performs its duties with unyielding accuracy and dedication, ensuring that your codebase remains in flawless condition. 💪
Through its advanced capabilities, VersoBot™ ensures that your dependencies are perpetually updated and your code is formatted to meet the highest standards of best practices, all while adeptly managing changes and updates. 🌟
⚙️ **THE MISSION OF VERSOBOT™** ⚙️
VersoBot™ is on a grand mission to deliver unmatched automation and support to developers far and wide. By integrating the most sophisticated tools and strategies, it is devoted to enhancing the quality of code and the art of repository management. 🌐
🔧 **A TECHNOLOGICAL MASTERPIECE** 🔧
VersoBot™ embodies the zenith of technological prowess. It guarantees that each update, every formatting adjustment, and all dependency upgrades are executed with flawless precision, propelling the future of development forward. 🚀
We extend our gratitude for your attention. Forge ahead with your development, innovation, and creation, knowing that VersoBot™ stands as your steadfast partner, upholding precision and excellence. 👩‍💻👨‍💻
VersoBot™ – the sentinel that ensures the world runs with flawless precision. 🌍💥
