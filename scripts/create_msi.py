#!/usr/bin/env python3
"""
Windows MSI installer creator for VidTanium
Uses WiX Toolset to create professional Windows installers
"""

import os
import sys
import subprocess
import uuid
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import BuildConfig, get_build_config, BuildProfile

class MSIBuilder:
    """Creates MSI installers using WiX Toolset"""
    
    def __init__(self, config: BuildConfig) -> None:
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build_msi"
        
    def check_wix_toolset(self) -> bool:
        """Check if WiX Toolset is available"""
        try:
            result = subprocess.run(["candle", "-?"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ WiX Toolset found")
                return True
        except FileNotFoundError:
            pass
        
        print("❌ WiX Toolset not found")
        print("💡 Install WiX Toolset from https://wixtoolset.org/")
        return False
    
    def generate_component_guid(self, component_name: str) -> str:
        """Generate deterministic GUID for component"""
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        return str(uuid.uuid5(namespace, f"{self.config.app_name}-{component_name}")).upper()
    
    def create_wxs_file(self) -> str:
        """Create WiX source file (.wxs)"""
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate GUIDs
        product_guid = self.generate_component_guid("product")
        upgrade_guid = self.generate_component_guid("upgrade")
        component_guid = self.generate_component_guid("main")
        
        # Determine executable path
        exe_source = self.dist_dir / f"{self.config.app_name}.exe"
        if not exe_source.exists():
            exe_source = self.dist_dir / self.config.app_name / f"{self.config.app_name}.exe"
        
        if not exe_source.exists():
            raise FileNotFoundError(f"Executable not found: {exe_source}")
        
        # Create WiX source
        wxs_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="{product_guid}" 
           Name="{self.config.app_name}" 
           Language="1033" 
           Version="{self.config.app_version}.0" 
           Manufacturer="{self.config.author}" 
           UpgradeCode="{upgrade_guid}">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine"
             Description="{self.config.description}"
             Comments="Built with VidTanium MSI Builder" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." />
    <MediaTemplate EmbedCab="yes" />
    
    <!-- Feature definition -->
    <Feature Id="ProductFeature" Title="{self.config.app_name}" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentRef Id="ApplicationShortcut" />
      <ComponentRef Id="DesktopShortcut" />
    </Feature>
    
    <!-- Directory structure -->
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="{self.config.app_name}" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="{self.config.app_name}" />
      </Directory>
      <Directory Id="DesktopFolder" Name="Desktop" />
    </Directory>
    
    <!-- Components -->
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="{component_guid}">
        <File Id="MainExe" 
              Source="{exe_source}" 
              KeyPath="yes"
              Checksum="yes">
          <Shortcut Id="StartMenuShortcut"
                    Directory="ApplicationProgramsFolder"
                    Name="{self.config.app_name}"
                    WorkingDirectory="INSTALLFOLDER"
                    Icon="ProductIcon"
                    IconIndex="0"
                    Advertise="yes" />
        </File>
        
        <!-- Registry entries -->
        <RegistryValue Root="HKCU" 
                       Key="Software\\{self.config.app_name}" 
                       Name="InstallDir" 
                       Type="string" 
                       Value="[INSTALLFOLDER]" 
                       KeyPath="no" />
        
        <RegistryValue Root="HKCU" 
                       Key="Software\\{self.config.app_name}" 
                       Name="Version" 
                       Type="string" 
                       Value="{self.config.app_version}" 
                       KeyPath="no" />
      </Component>
      
      <!-- Additional files -->
      <Component Id="DocumentationFiles" Guid="{self.generate_component_guid('docs')}">
        <File Id="ReadmeFile" Source="{self.project_root / 'README.md'}" KeyPath="yes" />
        <File Id="LicenseFile" Source="{self.project_root / 'LICENSE'}" />
        <File Id="ChangelogFile" Source="{self.project_root / 'CHANGELOG.md'}" />
      </Component>
    </ComponentGroup>
    
    <!-- Application shortcut -->
    <Component Id="ApplicationShortcut" Directory="ApplicationProgramsFolder" Guid="{self.generate_component_guid('shortcut')}">
      <Shortcut Id="ApplicationStartMenuShortcut"
                Name="{self.config.app_name}"
                Target="[#MainExe]"
                WorkingDirectory="INSTALLFOLDER"
                Icon="ProductIcon"
                IconIndex="0" />
      <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall" />
      <RegistryValue Root="HKCU" 
                     Key="Software\\{self.config.app_name}\\Shortcuts" 
                     Name="StartMenu" 
                     Type="integer" 
                     Value="1" 
                     KeyPath="yes" />
    </Component>
    
    <!-- Desktop shortcut -->
    <Component Id="DesktopShortcut" Directory="DesktopFolder" Guid="{self.generate_component_guid('desktop')}">
      <Shortcut Id="DesktopShortcut"
                Name="{self.config.app_name}"
                Target="[#MainExe]"
                WorkingDirectory="INSTALLFOLDER"
                Icon="ProductIcon"
                IconIndex="0" />
      <RegistryValue Root="HKCU" 
                     Key="Software\\{self.config.app_name}\\Shortcuts" 
                     Name="Desktop" 
                     Type="integer" 
                     Value="1" 
                     KeyPath="yes" />
    </Component>
    
    <!-- Icon -->
    <Icon Id="ProductIcon" SourceFile="{exe_source}" />
    
    <!-- Properties -->
    <Property Id="ARPPRODUCTICON" Value="ProductIcon" />
    <Property Id="ARPHELPLINK" Value="https://github.com/AstroAir/VidTanium" />
    <Property Id="ARPURLINFOABOUT" Value="https://github.com/AstroAir/VidTanium" />
    <Property Id="ARPNOREPAIR" Value="1" />
    <Property Id="ARPNOMODIFY" Value="1" />
    
    <!-- UI -->
    <UIRef Id="WixUI_InstallDir" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
    
    <!-- License -->
    <WixVariable Id="WixUILicenseRtf" Value="{self.project_root / 'LICENSE'}" />
    
  </Product>
</Wix>'''
        
        wxs_file = self.build_dir / f"{self.config.app_name}.wxs"
        with open(wxs_file, 'w', encoding='utf-8') as f:
            f.write(wxs_content)
        
        print(f"✅ Created WiX source file: {wxs_file}")
        return str(wxs_file)
    
    def build_msi(self, wxs_file: str) -> bool:
        """Build MSI from WiX source"""
        try:
            # Compile to .wixobj
            wixobj_file = self.build_dir / f"{self.config.app_name}.wixobj"
            
            print("🔨 Compiling WiX source...")
            result = subprocess.run([
                "candle", 
                "-out", str(wixobj_file),
                wxs_file
            ], cwd=self.build_dir, check=True, capture_output=True, text=True)
            
            # Link to .msi
            msi_name = f"{self.config.app_name}_v{self.config.app_version}_Setup.msi"
            msi_file = self.dist_dir / msi_name
            
            print("🔗 Linking MSI...")
            result = subprocess.run([
                "light",
                "-ext", "WixUIExtension",
                "-out", str(msi_file),
                str(wixobj_file)
            ], cwd=self.build_dir, check=True, capture_output=True, text=True)
            
            print(f"✅ Created MSI installer: {msi_file}")
            
            # Show file size
            if msi_file.exists():
                size_mb = msi_file.stat().st_size / 1024 / 1024
                print(f"📏 MSI size: {size_mb:.1f} MB")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ MSI build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

def main() -> None:
    """Main MSI builder function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Windows MSI installer builder")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile")
    
    args = parser.parse_args()
    
    # Get configuration
    profile = BuildProfile(args.profile)
    config = get_build_config(profile)
    
    print(f"🪟 Creating MSI installer for {config.app_name} v{config.app_version}")
    print(f"Profile: {config.profile.value}")
    print()
    
    # Create MSI builder
    builder = MSIBuilder(config)
    
    # Check WiX Toolset
    if not builder.check_wix_toolset():
        sys.exit(1)
    
    try:
        # Create WiX source file
        wxs_file = builder.create_wxs_file()
        
        # Build MSI
        if builder.build_msi(wxs_file):
            print("\n🎉 MSI installer created successfully!")
            print("\n💡 Next steps:")
            print("   • Test the MSI on a clean Windows system")
            print("   • Sign the MSI with a code signing certificate")
            print("   • Upload to distribution channels")
        else:
            print("\n❌ MSI creation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
