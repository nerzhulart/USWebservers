require 'rubygems'
require 'active_record'
require 'logger'

ActiveRecord::Base.logger = Logger.new(STDERR)
ActiveRecord::Base.colorize_logging = true

module SPbAU
  class SampleLogger
    class LoggerEntry < ActiveRecord::Base
    end

    def initialize
      ActiveRecord::Base.establish_connection(:adapter => "sqlite3",
                                              :database  => "serverlog")
      if !LoggerEntry.table_exists?
        ActiveRecord::Schema.define do
          create_table :logger_entries do |table|
            table.column :time, :string
            table.column :ip, :string
            table.column :filename, :string
            table.column :status_code, :integer
          end
        end
      end
    end

    def write(ip, filename, status_code)
      record = LoggerEntry.create(:time => Time.now.strftime("%c"),
                                  :ip => ip,
                                  :filename => filename, 
                                  :status_code => status_code)
    end

    def output
      entries = LoggerEntry.find(:all)
      for e in entries
        puts "#{e.time} #{e.ip} #{e.filename} #{e.status_code}"
      end
    end
  end
end
