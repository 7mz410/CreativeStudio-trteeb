//! trteeb saves documents as `.trteeb`, and upstream's `.designcraft` files still open.
//! Written by studio/rebrand.py.

use designcraft_engine::{Session, cmd};
use serde_json::json;

#[test]
fn save_writes_trteeb_and_designcraft_still_opens() {
    assert_eq!(cmd::with_document_extension("/d/Brochure"), "/d/Brochure.trteeb");
    assert_eq!(cmd::with_document_extension("/d/Brochure.designcraft"), "/d/Brochure.trteeb");

    let dir = std::env::temp_dir().join(format!("trteeb-extension-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let saved = dir.join("doc.trteeb");
    let mut session = Session::new();
    session.execute("file.new", &json!({})).unwrap();
    session.execute("file.saveAs", &json!({"path": saved.to_str().unwrap()})).unwrap();
    assert!(saved.exists(), "the save writes the .trteeb file");

    let old = dir.join("old.designcraft");
    std::fs::copy(&saved, &old).unwrap();
    let mut reopened = Session::new();
    reopened.execute("file.open", &json!({"path": old.to_str().unwrap()})).expect("a .designcraft file still opens");
    let _ = std::fs::remove_dir_all(&dir);
}
