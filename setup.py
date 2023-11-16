from setuptools import setup

setup(
    name="slack-dashboard",
    version="0.2.0",
    description="Slack dashboard",
    install_requires=[
        "slack-sdk==3.23.0",
        "appdirs==1.4.4",
    ],
    packages=['slack_dashboard'],
    entry_points={
        'console_scripts': [
            'slack-dashboard=slack_dashboard.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ]
)
