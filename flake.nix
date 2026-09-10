{
  description = "mdformat-pandoc - Mdformat plugin for Pandoc-style Markdown";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";

    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    treefmt-nix-config.url = "github:jkub6/treefmt-nix-config";
  };

  outputs = inputs @ {flake-parts, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      # 1. Define standard systems (including Mac)
      systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin"];

      # 2. Import the treefmt module globally for this flake
      imports = [
        inputs.treefmt-nix.flakeModule
      ];

      # 3. System-agnostic outputs (like overlays or NixOS modules) go here
      flake = {
        overlays.default = final: prev: {
          pythonPackagesExtensions =
            prev.pythonPackagesExtensions
            ++ [
              (python-final: python-prev: {
                mdformat-pandoc = python-final.buildPythonPackage {
                  pname = "mdformat-pandoc";
                  version = "0.1.0";
                  pyproject = true;

                  src = final.lib.cleanSource ./.;

                  propagatedBuildInputs = with python-final; [
                    mdformat
                    markdown-it-py
                    mdit-py-plugins
                    linkify-it-py
                  ];
                  nativeBuildInputs = [python-final.flit-core];
                  nativeCheckInputs = with python-final; [
                    pytestCheckHook
                    pytest-cov
                    pytest-xdist
                    pytest-randomly
                    pytest-timeout
                  ];

                  meta = with final.lib; {
                    description = "Mdformat support for pandoc syntax";
                    homepage = "https://github.com/jkub6/mdformat-pandoc";
                    license = licenses.mit;
                    mainProgram = "mdformat-pandoc";
                  };
                };
              })
            ];
        };
      };

      # 4. System-specific outputs go here
      perSystem = {
        config,
        pkgs,
        system,
        ...
      }: let
        # Apply our custom overlay to the local package set
        localPkgs = pkgs.extend inputs.self.overlays.default;
        python = localPkgs.python3;
      in {
        # Export the package
        packages.default = python.pkgs.mdformat-pandoc;

        # Export checks for CI
        checks = {
          build = python.pkgs.mdformat-pandoc;
        };

        # 5. treefmt works magically via the module system now
        treefmt = {
          imports = [inputs.treefmt-nix-config.treefmtModule];
        };

        # Export the development shell
        devShells.default = localPkgs.mkShell {
          inputsFrom = [python.pkgs.mdformat-pandoc];
          packages = with localPkgs; [
            just
            pandoc

            # Access the dynamically generated wrapper
            config.treefmt.build.wrapper

            (python.withPackages (p:
              with p; [
                mdformat-pandoc
                ruff
                mypy
                pytest
                pytest-cov
                pytest-xdist
                pytest-randomly
                pytest-timeout
                types-setuptools
                vulture
              ]))
          ];

          shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
          '';
        };
      };
    };
}
