import os
from unittest import mock

import pytest

from cloudinit import util
from cloudinit.net import netplan


@pytest.fixture
def renderer(tmp_path):
    config = {
        "netplan_path": str(tmp_path / "netplan/50-cloud-init.yaml"),
        "postcmds": True,
    }
    yield netplan.Renderer(config)


class TestNetplanRenderer:
    @pytest.mark.parametrize(
        "orig_config", ["", "{'orig_cfg': true}", "{'new_cfg': true}"]
    )
    def test_skip_netplan_generate(self, renderer, orig_config, mocker):
        """Check `netplan generate` called when netplan config has changed."""
        header = "\n"
        new_config = "{'new_cfg': true}"
        renderer_mocks = mocker.patch.multiple(
            renderer,
            _render_content=mocker.Mock(return_value=new_config),
            _netplan_generate=mocker.DEFAULT,
            _net_setup_link=mocker.DEFAULT,
        )
        if orig_config:
            util.ensure_dir(os.path.dirname(renderer.netplan_path))
            with open(renderer.netplan_path, "w") as f:
                f.write(header)
                f.write(orig_config)
        renderer.render_network_state(mocker.Mock())
        config_changed = bool(orig_config != new_config)
        assert renderer_mocks["_netplan_generate"].call_args_list == [
            mock.call(run=True, config_changed=config_changed)
        ]


class TestNetplanAPIWriteYAMLFile:
    def test_no_netplan_python_api(self, caplog):
        """Skip when no netplan available."""
        with mock.patch("builtins.__import__", side_effect=ImportError):
            netplan.netplan_api_write_yaml_file("network: {version: 2}")
        assert (
            "No netplan python module. Fallback to write"
            f" {netplan.CLOUDINIT_NETPLAN_FILE}" in caplog.text
        )
