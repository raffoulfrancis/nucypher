import os

import pytest_twisted
from twisted.internet import threads

from nucypher.cli.main import nucypher_cli
from nucypher.config.characters import FelixConfiguration
from nucypher.utilities.sandbox.constants import (
    TEMPORARY_DOMAIN,
    TEST_PROVIDER_URI,
    INSECURE_DEVELOPMENT_PASSWORD,
    MOCK_CUSTOM_INSTALLATION_PATH_2
)


@pytest_twisted.inlineCallbacks
def test_run_felix(click_runner, federated_ursulas):

    args = ('felix', 'init',
            '--config-root', MOCK_CUSTOM_INSTALLATION_PATH_2,
            '--network', TEMPORARY_DOMAIN,
            '--no-registry',
            '--provider-uri', TEST_PROVIDER_URI)

    user_input = f'{INSECURE_DEVELOPMENT_PASSWORD}\n{INSECURE_DEVELOPMENT_PASSWORD}'
    result = click_runner.invoke(nucypher_cli, args, input=user_input, catch_exceptions=False)
    assert result.exit_code == 0

    configuration_file_location = os.path.join(MOCK_CUSTOM_INSTALLATION_PATH_2, 'felix.config')

    def run_felix():
        args = ('felix', 'run',
                '--config-file', configuration_file_location,
                '--provider-uri', TEST_PROVIDER_URI,
                '--dry-run',
                '--no-registry')

        user_input = f'{INSECURE_DEVELOPMENT_PASSWORD}'
        result = click_runner.invoke(nucypher_cli, args, input=user_input, catch_exceptions=False)
        assert result.exit_code == 0
        return result

    def request_felix_landing_page(result):

        # Init an equal Felix to the already running one.
        felix_config = FelixConfiguration.from_configuration_file(filepath=configuration_file_location)
        felix_config.keyring.unlock(password=INSECURE_DEVELOPMENT_PASSWORD)
        felix = felix_config.produce()

        # Make a flask app
        web_app = felix.make_web_app()
        test_client = web_app.test_client()

        response = test_client.get('/')
        assert response == 200

    d = threads.deferToThread(run_felix)
    d.addCallback(request_felix_landing_page)
    yield d
