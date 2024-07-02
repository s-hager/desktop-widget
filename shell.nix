# echo "use nix" >> .envrc && direnv allow
# nix-direnv-reload

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    python3 
    qt6.full
    python311Packages.pyqt6
  ];

  shellHook = ''
    echo "desktop-widget Shell Started" | ${pkgs.lolcat}/bin/lolcat
  '';
}