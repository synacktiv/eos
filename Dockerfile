# docker build . -t symfony
# docker run -p 8000:8000 symfony
FROM debian

# Dependencies
RUN apt update
RUN apt install -y php php-cli php-common php-xml php-mysql php-sqlite3 php-intl composer wget

# Install Symfony CLI
RUN wget https://get.symfony.com/cli/installer -O - | bash
RUN mv /root/.symfony/bin/symfony /usr/local/bin/symfony

# Create project
RUN git config --global user.name "Your Name"
RUN git config --global user.email "you@example.com"
RUN symfony new --demo /demo

# Start server
WORKDIR /demo
ENTRYPOINT ["symfony", "server:start", "--no-tls"]
