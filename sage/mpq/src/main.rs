use std::{env, fs};
use wow_mpq::{Archive, ArchiveBuilder, FormatVersion, ListfileOption};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("extract") if args.len() == 5 => {
            let bytes = Archive::open(&args[2])?.read_file(&args[3])?;
            fs::write(&args[4], bytes)?;
        }
        Some("pack") if args.len() == 4 => {
            let mut builder = ArchiveBuilder::new()
                .version(FormatVersion::V1)
                .block_size(3)
                .default_compression(wow_mpq::compression::flags::ZLIB)
                .listfile_option(ListfileOption::None);
            for name in ["Spell.dbc", "SkillLineAbility.dbc"] {
                let bytes = fs::read(format!("{}/{}", args[2], name))?;
                builder = builder.add_file_data(bytes, &format!("DBFilesClient\\{name}"));
            }
            builder.build(&args[3])?;
            let mut archive = Archive::open(&args[3])?;
            for name in ["Spell.dbc", "SkillLineAbility.dbc"] {
                assert_eq!(archive.read_file(&format!("DBFilesClient\\{name}"))?,
                           fs::read(format!("{}/{}", args[2], name))?);
            }
            println!("Packed and read back both client tables.");
        }
        _ => return Err("usage: sage-mpq extract ARCHIVE MEMBER OUTPUT | pack DBC_DIR OUTPUT".into()),
    }
    Ok(())
}
