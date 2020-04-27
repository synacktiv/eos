"""Sources EOS plugin."""

import re
from io import BytesIO
from pathlib import Path

from lxml import etree
from requests import Request

from eos.plugins import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Sources EOS plugin.

    Extract the source code of a Symfony application by performing a class lookup in the Kernel cache file.
    """

    name = 'Project sources'
    requirements = '3.0.0'

    def run(self):
        """
        1. Read the XML Kernel cache file (name depending on the Symfony version).
        2. Extract classes paths from it.
        3. Request each file through the engine and save their content to the Symfony instance.
        4. Look for other class paths in 'use' PHP statements (not perfect)
        5. Loop while new findings appear
        """

        # Get XML Kernel cache file
        self.log.debug('Looking for Kernel cache container file at %s', self.symfony.kernel_container_cache)
        data = self.symfony.profiler.open(self.symfony.kernel_container_cache)
        if data is None:
            self.log.error('Could not find Kernel cache container file at %s', self.symfony.kernel_container_cache)
            return
        self.symfony.files[self.symfony.kernel_container_cache] = data

        # Extract paths
        paths = set(self.parse_kernel_cache(data))

        # Look for other class paths in already found files
        regex = re.compile(f'{self.symfony.namespace}\\\\[0-9A-Za-z_\\\\]+')
        for content in self.symfony.files.values():
            paths.update(self.class_to_path(cls) for cls in regex.findall(content))

        # Enqueue
        url = self.symfony.profiler.url('open')
        self.log.debug('Found %d potential files', len(paths))
        for path in paths:
            self.engine.queue.put(Request(method='GET', url=url, params={'line': 1, 'file': path}))

        again = True
        found = set()
        while again:
            again = False

            # Wait, gather an clear results
            self.engine.join()
            new = [response for response in self.engine.results if response.status_code != 404]
            found.update(response.request.params['file'] for response in new)
            self.engine.results.clear()

            # Save results while looking for other classes
            for response in new:
                data = self.symfony.profiler.parse_file_preview(response.text)

                if data is not None:
                    # Save
                    self.symfony.files[response.request.params['file']] = data

                    # Lookup
                    for file in (self.class_to_path(cls) for cls in regex.findall(data)):
                        if file not in found:
                            self.engine.queue.put(Request(method='GET', url=url, params={'line': 1, 'file': file}))
                            again = True

        # Display results
        if found:
            self.log.warning('Found the following source files:')
            for path in sorted(found):
                self.log.warning('  %s', path)
        else:
            self.log.info('Did not find any file')

    def parse_kernel_cache(self, data: str) -> list:
        """
        Extract App namespaces from the Kernel cache container file.

        The XML Kernel cache file contains a list of services with the associated classes. This list can be extracted
        to retrieve source code file paths. Namespaces can be extracted from the class attribute of service elements or
        the key attribute of argument elements.

        <services>
          <service id="kernel" class="App\\Kernel" public="true" synthetic="true">
            <tag name="routing.route_loader"/>
          </service>
          <service id="App\\Command\\AddUserCommand" class="App\\Command\\AddUserCommand">
            <tag name="console.command"/>
            <argument type="service" id="doctrine.orm.default_entity_manager"/>
            <argument type="service" id="security.user_password_encoder.generic"/>
            <argument type="service" id="App\\Utils\\Validator"/>
            <argument type="service" id="App\\Repository\\UserRepository"/>
            <call method="setName">
              <argument>app:add-user</argument>
            </call>
          </service>

        :param data: file content
        :return: list of source file paths relative to the application root
        """

        tree = etree.parse(BytesIO(data.encode()))
        root = tree.getroot()
        services = root.findall('.//service', namespaces=root.nsmap)
        arguments = root.findall('.//argument', namespaces=root.nsmap)

        classes = {service.attrib.get('class') for service in services}
        classes.update(argument.attrib.get('id', '').split(':')[0] for argument in arguments)
        classes.update(argument.attrib.get('key', '').split(':')[0] for argument in arguments)
        classes = set(filter(lambda ns: ns and ns.startswith(self.symfony.namespace + '\\'), classes))

        return [self.class_to_path(cls, self.symfony.root) for cls in classes]

    @staticmethod
    def class_to_path(cls, root='src'):
        """
        Convert a class path to a PHP file path.

        Replaces the root namespace with the root directory.

        :param cls: a PHP class path
        :param root: the root directory
        :return:
        """

        return str(Path(root, *cls.split('\\')[1:])) + '.php'
