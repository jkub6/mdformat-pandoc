{
  description = "mdformat-pandoc - Mdformat plugin for Pandoc-style Markdown";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }: let
    overlay = final: prev: {
      pythonPackagesExtensions =
        prev.pythonPackagesExtensions
        ++ [
          (python-final: python-prev: {
            mdformat-pandoc = python-final.buildPythonPackage {
              pname = "mdformat-pandoc";
              version = "0.1.0";
              format = "pyproject";
              src = ./.;

              propagatedBuildInputs = with python-final; [
                mdformat
                markdown-it-py
                mdit-py-plugins
                linkify-it-py
              ];
              nativeBuildInputs = [python-final.flit-core];
              doCheck = false;
            };
          })
        ];
    };
  in
    flake-utils.lib.eachSystem ["x86_64-linux" "aarch64-linux"] (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [overlay];
        };
        python-to-use = pkgs.python3;
      in {
        packages.default = pkgs.python3Packages.mdformat-pandoc;

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            just
            pandoc
            (python-to-use.withPackages (p: [
              p.mdformat-pandoc
              p.ruff
              p.mypy
              p.pytest
              p.types-setuptools
            ]))
          ];
        };
      }
    )
    // {
      overlays.default = overlay;
    };
}
