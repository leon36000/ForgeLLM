//! Dependency-free reader for the stdlib-only differential-oracle fixture.
//!
//! This is deliberately NOT a general JSON parser: the fixture schema is
//! fully controlled by `scripts/generate_reference_oracle_fixture.py`, so a
//! parser restricted to exactly that flat grammar (objects, arrays, plain
//! ASCII strings, small non-negative integers -- no floats, no escapes, no
//! unicode) is a smaller and more mechanically-checkable trust surface than
//! either pulling in `serde_json` (a new Cargo dependency for a single
//! fixture file) or hand-rolling arbitrary transcendental math in Rust. It
//! lives under `tests/`, so it never touches the crate's zero-dependency
//! production surface.
#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Object(BTreeMap<String, Value>),
    Array(Vec<Value>),
    String(String),
    Integer(i64),
}

#[derive(Debug)]
pub struct ParseError(pub String);

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "fixture parse error: {}", self.0)
    }
}

impl std::error::Error for ParseError {}

struct Parser<'a> {
    bytes: &'a [u8],
    position: usize,
}

impl<'a> Parser<'a> {
    fn new(text: &'a str) -> Self {
        Self {
            bytes: text.as_bytes(),
            position: 0,
        }
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.position).copied()
    }

    fn advance(&mut self) -> Option<u8> {
        let byte = self.peek()?;
        self.position += 1;
        Some(byte)
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\t' | b'\n' | b'\r')) {
            self.position += 1;
        }
    }

    fn expect(&mut self, expected: u8) -> Result<(), ParseError> {
        match self.advance() {
            Some(byte) if byte == expected => Ok(()),
            Some(byte) => Err(ParseError(format!(
                "expected {:?} at byte {}, found {:?}",
                expected as char,
                self.position - 1,
                byte as char
            ))),
            None => Err(ParseError(format!(
                "expected {:?}, found end of input",
                expected as char
            ))),
        }
    }

    fn parse_value(&mut self) -> Result<Value, ParseError> {
        self.skip_whitespace();
        match self.peek() {
            Some(b'{') => self.parse_object(),
            Some(b'[') => self.parse_array(),
            Some(b'"') => self.parse_string().map(Value::String),
            Some(byte) if byte == b'-' || byte.is_ascii_digit() => self.parse_integer(),
            Some(byte) => Err(ParseError(format!(
                "unexpected byte {:?} at position {}",
                byte as char, self.position
            ))),
            None => Err(ParseError("unexpected end of input".to_string())),
        }
    }

    fn parse_object(&mut self) -> Result<Value, ParseError> {
        self.expect(b'{')?;
        let mut entries = BTreeMap::new();
        self.skip_whitespace();
        if self.peek() == Some(b'}') {
            self.position += 1;
            return Ok(Value::Object(entries));
        }
        loop {
            self.skip_whitespace();
            let key = self.parse_string()?;
            self.skip_whitespace();
            self.expect(b':')?;
            let value = self.parse_value()?;
            if entries.insert(key.clone(), value).is_some() {
                return Err(ParseError(format!("duplicate object key {key:?}")));
            }
            self.skip_whitespace();
            match self.advance() {
                Some(b',') => continue,
                Some(b'}') => break,
                other => {
                    return Err(ParseError(format!(
                        "expected ',' or '}}' in object, found {other:?}"
                    )));
                }
            }
        }
        Ok(Value::Object(entries))
    }

    fn parse_array(&mut self) -> Result<Value, ParseError> {
        self.expect(b'[')?;
        let mut items = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some(b']') {
            self.position += 1;
            return Ok(Value::Array(items));
        }
        loop {
            items.push(self.parse_value()?);
            self.skip_whitespace();
            match self.advance() {
                Some(b',') => continue,
                Some(b']') => break,
                other => {
                    return Err(ParseError(format!(
                        "expected ',' or ']' in array, found {other:?}"
                    )));
                }
            }
        }
        Ok(Value::Array(items))
    }

    fn parse_string(&mut self) -> Result<String, ParseError> {
        self.expect(b'"')?;
        let start = self.position;
        loop {
            match self.advance() {
                Some(b'"') => break,
                Some(byte) if byte.is_ascii() && byte != b'\\' => continue,
                Some(b'\\') => {
                    return Err(ParseError(
                        "escape sequences are not supported by this restricted parser".to_string(),
                    ));
                }
                Some(_) => {
                    return Err(ParseError(
                        "non-ASCII byte in string; this restricted parser only accepts ASCII"
                            .to_string(),
                    ));
                }
                None => return Err(ParseError("unterminated string".to_string())),
            }
        }
        let end = self.position - 1;
        std::str::from_utf8(&self.bytes[start..end])
            .map(str::to_owned)
            .map_err(|error| ParseError(format!("invalid utf-8 in string: {error}")))
    }

    fn parse_integer(&mut self) -> Result<Value, ParseError> {
        let start = self.position;
        if self.peek() == Some(b'-') {
            self.position += 1;
        }
        let digits_start = self.position;
        while matches!(self.peek(), Some(byte) if byte.is_ascii_digit()) {
            self.position += 1;
        }
        if self.position == digits_start {
            return Err(ParseError("expected at least one digit".to_string()));
        }
        // This restricted grammar never emits floats (no '.' or 'e'); reject
        // them explicitly rather than silently truncating.
        if matches!(self.peek(), Some(b'.' | b'e' | b'E')) {
            return Err(ParseError(
                "floating-point literals are not supported by this restricted parser".to_string(),
            ));
        }
        let text = std::str::from_utf8(&self.bytes[start..self.position]).unwrap();
        text.parse::<i64>()
            .map(Value::Integer)
            .map_err(|error| ParseError(format!("invalid integer {text:?}: {error}")))
    }
}

pub fn parse(text: &str) -> Result<Value, ParseError> {
    let mut parser = Parser::new(text);
    let value = parser.parse_value()?;
    parser.skip_whitespace();
    if parser.position != parser.bytes.len() {
        return Err(ParseError(format!(
            "trailing content at byte {}",
            parser.position
        )));
    }
    Ok(value)
}

impl Value {
    pub fn as_object(&self) -> Result<&BTreeMap<String, Value>, ParseError> {
        match self {
            Value::Object(map) => Ok(map),
            other => Err(ParseError(format!("expected object, found {other:?}"))),
        }
    }

    pub fn as_array(&self) -> Result<&[Value], ParseError> {
        match self {
            Value::Array(items) => Ok(items),
            other => Err(ParseError(format!("expected array, found {other:?}"))),
        }
    }

    pub fn as_str(&self) -> Result<&str, ParseError> {
        match self {
            Value::String(text) => Ok(text.as_str()),
            other => Err(ParseError(format!("expected string, found {other:?}"))),
        }
    }

    pub fn as_integer(&self) -> Result<i64, ParseError> {
        match self {
            Value::Integer(value) => Ok(*value),
            other => Err(ParseError(format!("expected integer, found {other:?}"))),
        }
    }

    pub fn field<'a>(&'a self, key: &str) -> Result<&'a Value, ParseError> {
        self.as_object()?
            .get(key)
            .ok_or_else(|| ParseError(format!("missing required field {key:?}")))
    }
}

/// A tensor as decoded from the fixture: shape plus row-major f32 data,
/// exactly as `forgellm_reference::Tensor` expects.
pub struct FixtureTensor {
    pub shape: Vec<usize>,
    pub data: Vec<f32>,
}

fn parse_hex_f32(text: &str) -> Result<f32, ParseError> {
    if text.len() != 8 || !text.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(ParseError(format!(
            "expected an 8-hex-digit f32 bit pattern, found {text:?}"
        )));
    }
    let bits = u32::from_str_radix(text, 16)
        .map_err(|error| ParseError(format!("invalid hex {text:?}: {error}")))?;
    Ok(f32::from_bits(bits))
}

pub fn parse_tensor(value: &Value) -> Result<FixtureTensor, ParseError> {
    let shape = value
        .field("shape")?
        .as_array()?
        .iter()
        .map(Value::as_integer)
        .map(|result| {
            result.and_then(|n| {
                usize::try_from(n).map_err(|_| ParseError("negative shape dimension".to_string()))
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    let data = value
        .field("data_hex")?
        .as_array()?
        .iter()
        .map(Value::as_str)
        .map(|result| result.and_then(parse_hex_f32))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(FixtureTensor { shape, data })
}

/// One test case as decoded from the fixture.
pub struct FixtureCase {
    pub op: String,
    pub case_id: String,
    pub inputs: BTreeMap<String, Value>,
    pub expected: FixtureTensor,
    pub comparison_mode: String,
    pub tolerance_hex: Value,
}

pub fn parse_cases(text: &str) -> Result<Vec<FixtureCase>, ParseError> {
    let root = parse(text)?;
    let raw_cases = root.field("cases")?.as_array()?;
    let mut cases = Vec::with_capacity(raw_cases.len());
    for raw_case in raw_cases {
        let op = raw_case.field("op")?.as_str()?.to_owned();
        let case_id = raw_case.field("case_id")?.as_str()?.to_owned();
        let inputs = raw_case.field("inputs")?.as_object()?.clone();
        let expected = parse_tensor(raw_case.field("expected")?)?;
        let comparison = raw_case.field("comparison")?;
        let comparison_mode = comparison.field("mode")?.as_str()?.to_owned();
        let tolerance_hex = comparison
            .as_object()?
            .get("tolerance_hex")
            .cloned()
            .unwrap_or(Value::Array(Vec::new()));
        cases.push(FixtureCase {
            op,
            case_id,
            inputs,
            expected,
            comparison_mode,
            tolerance_hex,
        });
    }
    Ok(cases)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_a_minimal_object() {
        let value = parse(r#"{"a": 1, "b": "text", "c": [1, 2, 3]}"#).unwrap();
        let object = value.as_object().unwrap();
        assert_eq!(object.get("a").unwrap().as_integer().unwrap(), 1);
        assert_eq!(object.get("b").unwrap().as_str().unwrap(), "text");
        assert_eq!(object.get("c").unwrap().as_array().unwrap().len(), 3);
    }

    #[test]
    fn parse_hex_f32_round_trips_known_bit_patterns() {
        assert_eq!(parse_hex_f32("3f800000").unwrap(), 1.0_f32);
        assert_eq!(parse_hex_f32("bf800000").unwrap(), -1.0_f32);
        assert_eq!(parse_hex_f32("00000000").unwrap(), 0.0_f32);
    }

    #[test]
    fn rejects_wrong_length_hex() {
        assert!(parse_hex_f32("abc").is_err());
        assert!(parse_hex_f32("123456789").is_err());
    }

    #[test]
    fn rejects_non_hex_characters() {
        assert!(parse_hex_f32("zzzzzzzz").is_err());
    }

    #[test]
    fn rejects_trailing_content() {
        assert!(parse(r#"{"a": 1} garbage"#).is_err());
    }

    #[test]
    fn rejects_unterminated_string() {
        assert!(parse(r#"{"a": "unterminated"#).is_err());
    }

    #[test]
    fn rejects_duplicate_object_keys() {
        assert!(parse(r#"{"a": 1, "a": 2}"#).is_err());
    }

    #[test]
    fn rejects_escape_sequences() {
        assert!(parse(r#"{"a": "line\nbreak"}"#).is_err());
    }

    #[test]
    fn rejects_floating_point_literals() {
        assert!(parse(r#"{"a": 1.5}"#).is_err());
    }

    #[test]
    fn rejects_trailing_comma() {
        assert!(parse(r#"{"a": 1,}"#).is_err());
        assert!(parse(r#"[1, 2,]"#).is_err());
    }

    #[test]
    fn rejects_missing_colon() {
        assert!(parse(r#"{"a" 1}"#).is_err());
    }

    #[test]
    fn accepts_empty_object_and_array() {
        assert!(parse("{}").is_ok());
        assert!(parse("[]").is_ok());
    }

    #[test]
    fn field_reports_missing_key() {
        let value = parse(r#"{"a": 1}"#).unwrap();
        assert!(value.field("missing").is_err());
    }

    #[test]
    fn parse_cases_reads_a_realistic_minimal_fixture() {
        let text = r#"{
            "schema_version": "1.0",
            "cases": [
                {
                    "op": "elementwise_add",
                    "case_id": "basic",
                    "inputs": {"lhs": {"shape": [1], "data_hex": ["3f800000"]}},
                    "expected": {"shape": [1], "data_hex": ["40000000"]},
                    "comparison": {"mode": "exact"}
                }
            ]
        }"#;
        let cases = parse_cases(text).unwrap();
        assert_eq!(cases.len(), 1);
        assert_eq!(cases[0].op, "elementwise_add");
        assert_eq!(cases[0].expected.data, vec![2.0_f32]);
    }
}
