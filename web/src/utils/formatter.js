import moment from 'moment'
export function RandomStr(len = 8) {
  let charts = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".split('')
  let s = ''
  for (let i = 0; i < len; i++) s += charts[(Math.random() * 0x3e) | 0];
  return s;
}

export function FormatPrice(price, priceTick = 2) {
  if (typeof price === 'number') return price.toFixed(priceTick)
  else return price
}

export function FormatDirection(value) {
  switch (value) {
    case 'BUY':
      return '买'
    case 'SELL':
      return '卖'
    default:
      return value
  }
}

export function FormatOffset(value) {
  switch (value) {
    case 'OPEN':
      return '开'
    case 'CLOSE':
      return '平'
    case 'CLOSETODAY':
      return '平今'
    default:
      return value
  }
}

export function FormatStatus(value) {
  switch (value) {
    case 'ALIVE':
      return '未完成'
    case 'FINISHED':
      return '已完成'
    default:
      return value
  }
}

export function ObjectToArray(obj, arr, key, fn) {
  // key [string | function] return string
  // fn [function] return bool
  if (typeof obj !== 'object' || !Array.isArray(arr)) return
  let recordedItems = []
  for (let i = 0; i < arr.length; i++) {
    let v = arr[i]
    let key_field_name = typeof key === 'string' ? key : key(v)
    let k = arr[i][key_field_name]
    if (obj.hasOwnProperty(k) && fn(v)) {
      arr[i] = obj[k]
      recordedItems.push(k)
    } else {
      arr.splice(i--, 1);
    }
  }
  for (let k in obj) {
    if (!recordedItems.includes(k)) {
      let v = obj[k]
      if (fn(v)) {
        arr.push(v)
      }
    }
  }
}

export function ParseDurationToString (duration) {
  let parseString = ''
  if (duration && duration >= 1e9) {
    const dur = moment.duration(duration / 1e9, 'seconds')
    if (dur.years() > 0) parseString += dur.years() + 'Y'
    if (dur.months() > 0) parseString += dur.months() + 'M'
    if (dur.days() > 0) parseString += dur.days() + 'D'
    if (dur.hours() > 0) parseString += dur.hours() + 'h'
    if (dur.minutes() > 0) parseString += dur.minutes() + 'm'
    if (dur.seconds() > 0) parseString += dur.seconds() + 's'
  }
  return parseString
}

