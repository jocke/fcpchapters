require 'minitest/autorun'
load File.expand_path('../fcpchapters', __dir__)
class ChapterTests < Minitest::Test
  def test_intro_and_nonblocking_short_chapters
    p = {duration: Rational(96), chapters: [{title: 'First', time: Rational(19,2), id: 'a'}, {title: 'Last', time: Rational(88), id: 'b'}]}
    chapters, warnings = FCPChapters.render(p)
    assert_equal 'Intro', chapters.first[:title]
    assert_equal 3, chapters.length
    assert_equal 2, warnings.length
    assert_equal '00:09', FCPChapters.format_time(chapters[1][:time])
  end
  def test_existing_formatted_zero_does_not_add_intro
    p = {duration: Rational(60), chapters: [{title: 'Existing', time: Rational(1,2), id: 'a'}]}
    chapters, = FCPChapters.render(p)
    assert_equal ['Existing'], chapters.map { |c| c[:title] }
  end
  def test_duplicate_seconds_warn_without_dropping_titles
    p = {duration: Rational(60), chapters: [{title: 'A', time: Rational(0)}, {title: 'B', time: Rational(1,2)}]}
    chapters, warnings = FCPChapters.render(p)
    assert_equal 2, chapters.length
    assert warnings.any? { |w| w.include?('Duplicate timestamp') }
  end
  def test_empty_project_has_no_intro_or_chapter_warnings
    assert_equal [[], []], FCPChapters.render({duration: Rational(60), chapters: []})
  end
  def test_intro_requires_enough_distinct_timestamps
    one = [{title: 'One', time: Rational(20)}]
    chapters, warnings = FCPChapters.render({duration: Rational(60), chapters: one})
    assert_equal one, chapters
    assert warnings.any? { |w| w.include?('at least three') }
    duplicate = one + [{title: 'Same second', time: Rational(201,10)}]
    chapters, = FCPChapters.render({duration: Rational(60), chapters: duplicate})
    assert_equal duplicate, chapters
    two = one + [{title: 'Two', time: Rational(40)}]
    chapters, = FCPChapters.render({duration: Rational(60), chapters: two})
    assert_equal ['Intro', 'One', 'Two'], chapters.map { |c| c[:title] }
  end
  def test_long_time_and_invalid_data
    assert_equal '1:01:01', FCPChapters.format_time(Rational(36619,10))
    assert_raises(FCPChapters::Error) { FCPChapters.pair('{(0/0),(1/1)}') }
    assert_raises(FCPChapters::Error) { FCPChapters::Plist.new('bad') }
  end
end

class CLIIntegrationTests < Minitest::Test
  def setup
    @fixture = ENV['FCPCHAPTERS_TEST_LIBRARY']
    skip 'Set FCPCHAPTERS_TEST_LIBRARY to the sample bundle for integration tests' unless @fixture
    @script = File.expand_path('../fcpchapters', __dir__)
  end
  def run_cli(path, *args)
    Open3.capture3(RbConfig.ruby, @script, path, *args)
  end
  def test_report_plain_and_json
    out, err, status = run_cli(@fixture)
    assert status.success?, err
    assert_includes out, 'fcpchapters 0.5.17'
    assert_includes out, 'Found 5 chapter markers; added 1 Intro chapter; 6 entries in output.'
    assert_includes out, "\n------------------------------------------------------------\n00:00 Intro"
    assert_includes err, 'Warnings — "Basic Project" (2)'
    plain, _, status = run_cli(@fixture, '--plain')
    assert status.success?
    assert_equal 6, plain.lines.length
    assert plain.start_with?('00:00 Intro')
    json, _, status = run_cli(@fixture, '--json')
    assert status.success?
    data = JSON.parse(json)
    assert_equal '19/2', data['chapters'][1]['seconds']
    assert_equal '333/10', data['chapters'][2]['seconds']
  end
  def test_older_version_label_and_missing_schema
    require 'fileutils'
    Dir.mktmpdir do |dir|
      copy = File.join(dir, 'Test.fcpbundle')
      FileUtils.cp_r(@fixture, copy)
      _, err, status = Open3.capture3('/usr/bin/plutil', '-replace', 'catalogVersion', '-string', 'older-test-version', File.join(copy, 'CurrentVersion.plist'))
      assert status.success?, err
      out, err, status = run_cli(copy, '--plain')
      assert status.success?, err
      assert_equal 6, out.lines.length
      assert_includes err, 'has not been tested'
      db = Dir.glob(File.join(copy, '**', 'CurrentVersion.fcpevent')).first
      _, _, status = Open3.capture3('/usr/bin/sqlite3', db, 'ALTER TABLE ZCOLLECTION RENAME COLUMN ZTYPE TO MISSING_TYPE;')
      assert status.success?
      out, err, status = run_cli(copy, '--plain')
      refute status.success?
      assert_empty out
      assert_includes err, 'Errors'
      assert_includes err, 'ZCOLLECTION missing ZTYPE'
    end
  end
end
