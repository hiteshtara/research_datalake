import click, yaml
from src.main import run_module

@click.group()
def cli(): pass

@cli.command()
@click.option('--module', default='irb')
def run(module):
    cfg = yaml.safe_load(open('./config/settings.yaml'))
    run_module(module, cfg)

if __name__ == '__main__':
    cli()
